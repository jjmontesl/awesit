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
from sitetool.files.files import SiteFile
import fabric
import pathspec


logger = logging.getLogger(__name__)


class SSHFiles():
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

    def initialize(self):
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

    def file_matches(self, rel_path, excludes):
        matches = False
        if excludes:
            spec = pathspec.PathSpec.from_lines('gitwildmatch', excludes)
            if spec.match_file(rel_path[1:]):
                matches = True
        return matches

    def file_excluded(self, rel_path):

        excludes = self.exclude

        return self.file_matches(rel_path, excludes)

    def file_list(self, remote_path, depth=None):

        final_path = os.path.join(self.path, remote_path)
        logger.debug("Listing files through SSH: %s@%s:%s", self.get_user(), self.host, final_path)

        # FIXME: Redirect output to file and get file through get to avoid spurious outputs to stdout breaking find outuput
        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            output = None
            try:
                if self.sudo:
                    output = c.sudo('[ -d "%s" ] && cd "%s" && sudo TZ=utc find "%s" -type f -printf \'%%T+,%%T+,%%s,%%p\\n\'' % (final_path, self.path, final_path), hide=True)  # hide=not self.st.debug, echo=not self.st.debug)
                else:
                    output = c.run('[ -d "%s" ] && cd "%s" && TZ=utc find "%s" -type f -printf \'%%T+,%%T+,%%s,%%p\\n\'' % (final_path, self.path, final_path), hide=True)  # not self.st.debug, echo=not self.st.debug)
                output = output.stdout.strip()
            except Exception as e:
                # Assume the directory does not exist, but this is bad error handling
                #logger.warn("Error while listing files through SSH: %s" % e)
                output = ''

        result = []
        for line in output.split("\n"):
            if not line: continue
            try:
                (ctime, mtime, size, path) = line.split(",", 3)
            except Exception as e:
                logger.warn("Error parsing SSH file list data: %s (line: %r)" % (e, line))
                continue

            file_path_abs = path
            file_path_rel = "/" + file_path_abs[len(final_path):]


            excluded = self.file_excluded(file_path_rel)
            if excluded:
                continue

            mtime = datetime.datetime.strptime(ctime.split(".")[0], '%Y-%m-%d+%H:%M:%S')
            mtime = mtime.replace(tzinfo=pytz.utc)

            result.append(SiteFile(file_path_rel, int(size), mtime))

        return result

    def archive(self):
        """
        Archives files and provides a remote path for the archive file.
        """
        logger.info("Archiving files through SSH from %s@%s:%s/%s", self.get_user(), self.host, self.port, self.path)

        remote_backup_path = tempfile.mktemp(prefix='sitetool-tmp-files-remote-backup-')  # FIXME: shall be a remote tmporary file

        backup_md5sum = None

        with fabric.Connection(host=self.host, port=self.port, user=self.get_user()) as c:
            # --files-from files.txt
            if self.sudo:
                c.sudo("tar czf %s -C %s ." % (remote_backup_path, self.path))
            else:
                c.run("tar czf %s -C %s ." % (remote_backup_path, self.path))

        backup_path = self.file_get(remote_backup_path, base_path="/")
        self.file_delete(remote_backup_path, base_path="/")

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

