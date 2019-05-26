# SiteTool

import subprocess
import logging
import os
import shutil
from tempfile import mktemp
import tempfile
import errno
import stat
import datetime


logger = logging.getLogger(__name__)


class LocalFiles():
    '''
    '''

    path = None
    ignore = None

    def file_get(self, remote_path):
        local_path = tempfile.mktemp(prefix='sitetool-tmp-')
        final_path = os.path.expanduser(os.path.join(self.path, remote_path))
        logger.debug("Reading file %s from local to: %s", final_path, local_path)
        shutil.copyfile(final_path, local_path)
        return local_path

    def file_put(self, local_path, remote_path):
        final_path = os.path.expanduser(os.path.join(self.path, remote_path))
        logger.debug("Writing file %s to local: %s", local_path, final_path)
        try:
            os.makedirs(os.path.dirname(final_path))
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(os.path.dirname(final_path)):
                pass
            else:
                raise

        shutil.copyfile(local_path, final_path)

    def file_delete(self, remote_path):
        final_path = os.path.expanduser(os.path.join(self.path, remote_path))
        logger.debug("Deleting: %s", final_path)
        os.unlink(final_path)

    def file_list(self, remote_path, depth=None):
        final_path = os.path.expanduser(os.path.join(self.path, remote_path))

        result = []
        for root, dirs, files in os.walk(final_path):
            #path = root.split(os.sep)
            #print((len(path) - 1) * '---', os.path.basename(root))
            for file in files:
                #print(file)

                file_path_abs = os.path.join(root, file)
                file_path_rel = "/" + file_path_abs[len(final_path):]

                matches = False
                if self.ignore:
                    for ignore in self.ignore:
                        if file_path_rel.startswith(ignore):
                            matches = True
                            break
                if matches:
                    continue

                try:
                    stats = os.stat(os.path.join(root, file))
                    result.append((root, file,
                                   stats[stat.ST_SIZE],
                                   datetime.datetime.fromtimestamp(stats[stat.ST_CTIME]),
                                   datetime.datetime.fromtimestamp(stats[stat.ST_MTIME])))
                except Exception as e:
                    logger.warn(e)

        return result

    def archive(self):
        """
        Archives files and provide a path for the archive file.
        """
        backup_path = "/tmp/sitetool-files-backup.tgz"

        logger.info("Archiving files (local) from %s to %s", self.path, backup_path)
        subprocess.call(["tar", "czf", backup_path, '-C', self.path, '.'])

        backup_md5sum = None

        return (backup_path, backup_md5sum)

    def restore(self, path):
        """
        Restores files.
        """
        final_path = os.path.expanduser(self.path)
        logger.info("Restoring files (local) from %s to %s", path, final_path)

        try:
            os.makedirs(os.path.dirname(final_path))
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(os.path.dirname(final_path)):
                pass
            else:
                raise

        subprocess.call(["tar", "xf", path, '-C', final_path])
