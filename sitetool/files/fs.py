# SiteTool

from dateutil import tz
import datetime
import logging
import os
import requests
import time

import fs
import pytz

from sitetool.files.files import SiteFile

logger = logging.getLogger(__name__)


class FSFiles():
    '''
    This driver can access several filesystem types (local, FTP, SFTP, SCP, FTPS, HTTP...).
    '''

    url = None
    exclude = None
    path = None

    ignore_list_errors = False

    def file_list(self, remote_path, depth=None):

        self.path = self.url

        url = self.url
        final_path = url  # os.path.join(self.path, remote_path)

        logger.debug("Retrieving filelist through FS connector (url: %s)", url)

        try:
            remote_fs = fs.open_fs(url)
        except Exception as e:
            if not self.ignore_list_errors:
                logger.warn("Could not open filesystem: %s", url)
            else:
                logger.debug("Could not open filesystem: %s", url)
            return None

        result = []
        for (path, info) in remote_fs.walk.info(namespaces=['details']):

            if info.is_dir: continue

            #with fs.open(path) as python_file:
                #count += sum(1 for line in python_file if line.strip())

            file_path_abs = path
            file_path_rel = "/" + file_path_abs[len(final_path):]

            matches = False
            if self.exclude:
                for exclude in self.exclude:
                    if file_path_rel.startswith(exclude):
                        matches = True
                        break
            if matches:
                continue

            mtime_utc = info.modified.astimezone(pytz.utc)

            #local_zone = tz.tzlocal()
            #modified = info.modified.astimezone(to_zone)
            #modified = datetime.datetime.fromtimestamp(time.mktime(modified.timetuple()))

            result.append(SiteFile(file_path_rel, info.size, mtime_utc))

        return result

    def archive(self):
        """
        Archives files and provide the archived file.
        """
        raise NotImplementedError("FSFiles does not implement an archive operation.")

