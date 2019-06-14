# SiteTool

from dateutil import tz
import datetime
import getpass
import logging
import os
import pytz
import subprocess
import tempfile
import warnings

from sitetool.core.exceptions import SiteToolException
from sitetool.files.files import Files, SiteFile, SiteFileList
import fabric
import pathspec


logger = logging.getLogger(__name__)


class SSHFiles(Files):
    '''
    '''

    path = None

    exclude = None

    user = None
    password = None
    host = None
    port = 22

    sudo = False

    #password = None
    #key = None

    def initialize(self, ctx, site):
        super().initialize(ctx, site)
        if self.host is None:
            raise SiteToolException("No host set for SSHFiles: %s", self)

    def get_user(self):
        if self.user is None:
            return getpass.getuser()
        return self.user

    def file_get(self, remote_path, base_path=None):
        if base_path is None: base_path = self.path
        final_path = os.path.join(base_path, remote_path)
        local_path = tempfile.mktemp(prefix='sitetool-tmp-')
        logger.info("Getting file via SSH from %s@%s:%s to %s", self.get_user(), self.host, final_path, local_path)

        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            c.get(final_path, local_path)

        return local_path

    def file_put(self, local_path, remote_path):
        final_path = os.path.join(self.path, remote_path)
        logger.debug("Writing file via SSH from %s to %s@%s:%s", local_path, self.get_user(), self.host, final_path)

        # Create dir
        dirname = os.path.dirname(final_path)
        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            if self.sudo:
                c.sudo('mkdir -p "%s"' % dirname)
            else:
                c.run('mkdir -p "%s"' % dirname)

        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            result = c.put(local_path, final_path)

    def file_delete(self, remote_path, base_path="/"):
        if base_path is None: base_path = self.path
        final_path = os.path.join(base_path, remote_path)
        logger.debug("Deleting via SSH: %s@%s:%s", self.get_user(), self.host, final_path)

        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            if self.sudo:
                c.sudo('rm "%s"' % final_path)
            else:
                c.run('rm "%s"' % final_path)

    def file_list(self, remote_path, all=False, depth=None):

        final_path = os.path.join(self.path, remote_path)
        logger.debug("Listing files through SSH: %s@%s:%s", self.get_user(), self.host, final_path)

        # FIXME: Redirect output to file and get file through get to avoid spurious outputs to stdout breaking find outuput
        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            output = None
            try:
                if self.sudo:
                    output = c.sudo('[ -d "%s" ] && cd "%s" && sudo TZ=utc find "%s" -type f -ignore_readdir_race -printf \'%%T+,%%T+,%%s,%%p\\n\' || true' % (final_path, self.path, final_path), hide=True)  # hide=not self.st.debug, echo=not self.st.debug)
                else:
                    output = c.run('[ -d "%s" ] && cd "%s" && TZ=utc find "%s" -type f -ignore_readdir_race -printf \'%%T+,%%T+,%%s,%%p\\n\' || true' % (final_path, self.path, final_path), hide=True)  # not self.st.debug, echo=not self.st.debug)
                result = output
                output = result.stdout.strip()
                errors = result.stderr.strip()
            except Exception as e:
                logger.debug("Error while listing files through SSH: %s", e)
                raise SiteToolException("Error while listing files through SSH: %s" % e)

        if errors:
            #logger.warn("Errors listing files: %s", errors)
            errors = errors.split("\n")

        result = []
        for line in output.split("\n"):
            if not line: continue
            try:
                (ctime, mtime, size, path) = line.split(",", 3)
            except Exception as e:
                logger.warn("Error parsing SSH file list data: %s (line: %r)" % (e, line))
                continue

            file_path_abs = path
            file_path_rel = file_path_abs[len(final_path):]

            mtime = datetime.datetime.strptime(ctime.split(".")[0], '%Y-%m-%d+%H:%M:%S')
            mtime = mtime.replace(tzinfo=pytz.utc)

            result.append(SiteFile(file_path_rel, int(size), mtime))

        # Excludes
        if not all:
            result = self.files_filtered(result)

        return SiteFileList(result, errors)

    def archive(self):
        """
        Archives files and provides a remote path for the archive file.
        """
        logger.info("Archiving files through SSH from %s@%s:%s/%s", self.get_user(), self.host, self.port, self.path)

        remote_backup_path = tempfile.mktemp(prefix='sitetool-tmp-files-remote-backup-')  # FIXME: shall be a remote tmporary file

        backup_md5sum = None

        logger.info("Resolving files to be archived.")
        filelist, errors = self.file_list('')
        size = sum([f.size for f in filelist]) if filelist else 0

         # Write filelist to file
        filelist_path = tempfile.mktemp(prefix='sitetool-tmp-files-backup-filelist-')
        remote_filelist_path = tempfile.mktemp(prefix='sitetool-tmp-files-backup-filelist-remote-')
        with open(filelist_path, "w") as f:
            f.write("\n".join([x.relpath for x in filelist]))

        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:

            # Upload filelist
            logger.info("Uploading filelist.")
            c.put(filelist_path, remote_filelist_path)

            logger.info("Archiving %d files (%.1fM) via SSH.", len(filelist), size / (1024 * 1024))
            if self.sudo:
                c.sudo('tar czf "%s" -C "%s" --ignore-failed-read --files-from "%s"' % (remote_backup_path, self.path, remote_filelist_path))
                c.sudo('rm "%s"' % (remote_filelist_path))
            else:
                c.run('tar czf "%s" -C "%s" --ignore-failed-read --files-from "%s"' % (remote_backup_path, self.path, remote_filelist_path))
                c.run('rm "%s"' % (remote_filelist_path))

        backup_path = self.file_get(remote_backup_path, base_path="/")
        self.file_delete(remote_backup_path, base_path="/")

        os.unlink(filelist_path)

        return (backup_path, backup_md5sum)

    def restore(self, path):
        """
        Restores files.
        """
        final_path = self.path
        logger.info("Restoring files through SSH from %s to %s@%s:%s", path, self.get_user(), self.host, final_path)

        backup_path = "/tmp/sitetool-files-backup.tgz"
        self.file_put(path, backup_path)

        # Create dir
        dirname = final_path
        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            if self.sudo:
                c.sudo('mkdir -p "%s"' % dirname)
                c.sudo('tar xf %s -C %s' % (backup_path, dirname))
            else:
                c.run('mkdir -p "%s"' % dirname)
                c.run('tar xf %s -C %s' % (backup_path, dirname))

