# SiteTool

import argparse
import datetime
import logging
import os

from sitetool.files.backup import BackupManager
from sitetool.sites import Site
import sys


logger = logging.getLogger(__name__)


class DeployCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description='Deploys a backup to a given environment')
        parser.add_argument("source", help="backupsite:env:site:env - source backup and backed up environment")
        parser.add_argument("target", help="site:env - target backup site and environment")

        args = parser.parse_args(args)

        self.src = args.source
        self.dst = args.target

    def run(self):
        """
        A backup copies different items (files, databases...) and generates
        a single "archived artifact" for each.
        """

        self.ctx = self.st.config
        backupmanager = BackupManager(self.st)

        #(backup_site_name, backup_site_env) = self.src.split(":")[0:2]
        #(src_site_name, src_site_env) = self.src.split(":")[2:4]
        (target_site_name, target_site_env) = Site.parse_site_env(self.dst)

        jobs = backupmanager.list_backups(self.src)

        if len(jobs) == 0:
            logger.error("No backup jobs found for expression: %s", self.src)
            sys.exit(3)
        elif len(jobs) > 1:
            logger.error("More than one backup jobs (%d) found for expression: %s (cannot deploy multiple backups! tru 'backup-list')", len(jobs), self.src)
            sys.exit(3)

        job = jobs[0]

        logger.info("Restoring %s from: %s to: %s", job, self.src, self.dst)

        backup_site = job.env_backup
        src_site = job.env_site
        target_site = self.ctx['sites'][target_site_name]['envs'][target_site_env]

        # Copy and restore files
        backup_path = '%s/%s/%s' % (src_site['site']['name'], src_site['name'], job.filename)
        tmpfile_path = backup_site['files'].file_get(backup_path)

        target_site['files'].restore(tmpfile_path)
        os.unlink(tmpfile_path)

        # Restore database
