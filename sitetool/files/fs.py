# SiteTool

from dateutil import tz
import datetime
import logging
import os
import requests
import time

import fs
import pytz

from sitetool.files.files import Files, SiteFile, SiteFileList
import json

logger = logging.getLogger(__name__)


class FSFiles(Files):
    '''
    This driver can access several filesystem types (local, FTP, SFTP, SCP, FTPS...).

    It relies on the PyFilesystem library (https://github.com/PyFilesystem/pyfilesystem2).
    '''

    url = None
    exclude = None
    path = None

    ignore_list_errors = False

    def file_list(self, remote_path, all=None):

        self.path = self.url

        url = self.url + remote_path

        logger.debug("Retrieving filelist through FS connector (url: %s)", url)

        try:
            remote_fs = fs.open_fs(url)
        except Exception as e:
            if not self.ignore_list_errors:
                logger.warn("Could not open filesystem: %s", url)
            else:
                logger.debug("Could not open filesystem: %s", url)
            return None

        def fs_walk_error(path, e):
            real_exc = e.exc
            #real_path = real_exc.path  # remote_fs.getsyspath(e.path)
            #print(real_exc.filename)
            logger.warn("Could not access path '%s': %s (%s)" % (path, e, real_exc))
            #return True  # Ignore error
            return False

        #for (path, info) in remote_fs.walk.info(on_error=fs_walk_error):
        #    print(path)

        result = []
        #for (path, info) in remote_fs.walk.info(namespaces=['details'], on_error=fs_walk_error):
        for (path, info) in remote_fs.walk.info(on_error=fs_walk_error):

            if info.is_dir: continue

            file_path_abs = path
            file_path_rel = path[1:]

            try:
                info = remote_fs.getinfo(path, namespaces=['details'])
            except Exception as e:
                logger.warn("Could not obtain information of file: %s", file_path_rel)
                continue

            mtime_utc = info.modified.astimezone(pytz.utc)

            #local_zone = tz.tzlocal()
            #modified = info.modified.astimezone(to_zone)
            #modified = datetime.datetime.fromtimestamp(time.mktime(modified.timetuple()))

            result.append(SiteFile(file_path_rel, info.size, mtime_utc))

        # Excludes
        if not all:
            result = self.files_filtered(result)

        return SiteFileList(result, [])

    def archive(self):
        """
        Archives files and provide the archived file.
        """
        raise NotImplementedError("FSFiles does not implement an archive operation.")

