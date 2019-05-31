# SiteTool

import os
import requests
import sys
import json
import datetime
import logging
import tempfile
import pytz

from sitetool.files.files import SiteFile, Files


logger = logging.getLogger(__name__)


class PHPFiles(Files):
    '''
    '''

    url = None

    ignore_list_errors = False

    def file_list(self, remote_path, all=False, depth=None):

        final_path = os.path.join(self.path, remote_path)

        url = self.url
        data = {'secret': self.secret,
                'command': 'file_list',
                'path': final_path}

        logger.debug("Retrieving filelist through PHP connector (url: %s, path: %s)", url, final_path)

        # TODO: Check response code

        try:
            r = requests.post(url, data)
            fileinfo = json.loads(r.text)
        except Exception as e:
            if not self.ignore_list_errors:
                logger.warn("Could not retrieve filelist information from PHP connector (%s): %s", url, e)
            else:
                logger.debug("Could not retrieve filelist information from PHP connector (%s): %s", url, e)
            return None

        result = []
        for file in fileinfo:

            file_path_abs = file[3]
            file_path_rel = file_path_abs[len(final_path):]

            #ctime = datetime.datetime.fromtimestamp(file[0]).replace(tzinfo=pytz.utc)
            #ctime = datetime.datetime.strptime(file[0], '%Y-%m-%d+%H:%M:%S').replace(tzinfo=pytz.utc)
            mtime = datetime.datetime.strptime(file[1], '%Y-%m-%d+%H:%M:%S').replace(tzinfo=pytz.utc)

            result.append(SiteFile(file_path_rel, file[2], mtime))

        # Excludes
        if not all:
            result = self.files_filtered(result)

        return result

    def archive(self):
        """
        Archives files and returns a path for the archive file.
        """
        backup_path = tempfile.mktemp(prefix='sitetool-tmp-')

        final_path = os.path.join(self.path)

        logger.info("Resolving files to be archived.")
        filelist = self.file_list('')
        size = sum([f.size for f in filelist]) if filelist else 0

        url = self.url
        data = {'secret': self.secret,
                'command': 'file_backup',
                'path': final_path,
                'filelist': [f.relpath for f in filelist]}

        logger.info("Archiving %d files (%.1fM) through PHP connector (url: %s, path: %s)", len(filelist), size / (1024 * 1024), url, final_path)

        r = requests.post(url, data)

        with open(backup_path, "wb") as f:
            f.write(r.content)

        backup_md5sum = None
        return (backup_path, backup_md5sum)

    def restore(self, path):
        """
        Restores files.
        """
        raise NotImplementedError()

