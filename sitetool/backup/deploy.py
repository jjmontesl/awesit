# SiteTool

import argparse
import datetime
import logging
import os
import sys

from sitetool.backup.backup import BackupListCommand
from sitetool.backup.backup import BackupManager
from sitetool.sites import Site


logger = logging.getLogger(__name__)


class BackupDeployCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Deploys a backup to a given environment'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("source", help="[backupsite:env:]site:env:job - source backup job")
        parser.add_argument("target", nargs='?', help="site:env - target deployment site and environment")
        parser.add_argument("-l", "--list", action="store_true", default=False, help="list the selected backup(s) and exit")

        args = parser.parse_args(args)

        self.src = args.source
        self.dst = args.target
        self.list = args.list

    def run(self):
        """
        A backup copies different items (files, databases...) and generates
        a single "archived artifact" for each.
        """

        if self.list:
            logger.info("Listing backups that would be selected by this filter:")
            command = BackupListCommand(self.ctx)
            command.src = self.src
            return command.run()

        backupmanager = self.ctx.get('backups')
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
        target_site = self.ctx.get('sites').site_env(target_site_name, target_site_env)

        # Copy and restore files
        job_filename = os.path.basename(job.relpath)
        backup_path = '%s/%s/%s' % (src_site.site.name, src_site.name, job_filename)
        tmpfile_path = backup_site.comp('files').file_get(backup_path)

        # TODO: type shall be defined by BackupManager
        if job_filename.endswith('-files.tar.gz'):

            target_site.comp('files').restore(tmpfile_path)
            os.unlink(tmpfile_path)

        elif job_filename.endswith('-db.tar.gz'):

            target_site.comp('db').restore(tmpfile_path)
            os.unlink(tmpfile_path)

