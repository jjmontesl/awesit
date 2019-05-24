# SiteTool

import argparse
import logging
import datetime

from sitetool.sites import Site
import os
import stat
from collections import namedtuple

logger = logging.getLogger(__name__)


class BackupCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description='Perform a files backup from a given site')
        parser.add_argument("src", help="site:env - source site and environment")
        parser.add_argument("dst", nargs='?', default='backup:default', help="site:env - target backup site and environment")

        args = parser.parse_args(args)

        self.src = args.src
        self.dst = args.dst

    def run(self):
        """
        A backup copies different items (files, databases...) and generates
        a single "archived artifact" for each.
        """

        self.ctx = self.st.config

        dt_start = datetime.datetime.utcnow()

        (src_site_name, src_site_env) = Site.parse_site_env(self.src)
        (backup_site_name, backup_site_env) = Site.parse_site_env(self.dst)

        backup_date = datetime.datetime.now()
        backup_job_name = backup_date.strftime('%Y%m%d-%H%M%S')

        src_site = self.ctx['sites'][src_site_name]['envs'][src_site_env]

        logger.info("Backup %s to %s", self.src, self.dst)

        # TODO: Objects should define their backup artifacts (from 0 to N)

        # Copy files
        (files_path, files_hash) = src_site['files'].archive()
        #logger.info("Backup remote file path: %s (hash: %x)", files_path, files_hash or 0)

        tmpfile_path = src_site['files'].file_get(files_path)
        stats = os.stat(tmpfile_path)
        backup_size = stats[stat.ST_SIZE]

        # Copy backup file to place
        backup_site = self.ctx['sites'][backup_site_name]['envs'][backup_site_env]
        #backup_root_dir = '/home/jjmontes/sitetool/backup/'
        backup_path = '%s/%s/%s-%s-%s-files.tar.gz' % (src_site_name, src_site_env, src_site_name, src_site_env, backup_job_name)

        backup_site['files'].file_put(tmpfile_path, backup_path)

        src_site['files'].file_delete(files_path)

        # Copy database
        if 'db' in src_site:
            self._backup_database(src_site)

        backup_time = (datetime.datetime.utcnow() - dt_start).total_seconds()

        logger.info("Backup finished (time: %.1fm, size=%.2fMB)", backup_time / 60.0, backup_size / (1024 * 1024))

    def _backup_database(self, src_site):

        db_path = src_site['db'].dump()
        logger.info("Backup db path: %s", db_path)

        # Copy database file to place


class BackupListCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description='Show available backup jobs')
        parser.add_argument("src", default="::::", nargs='?', help="backupsite:env:site:env - source backup and site environments")

        args = parser.parse_args(args)

        self.src = args.src

    def run(self):
        """
        """

        self.ctx = self.st.config
        backupmanager = BackupManager(self.st)
        backups = backupmanager.list_backups(self.src)

        idx = 0
        total_size = 0
        for backup in backups:
            idx += 1
            total_size += backup.size
            print("%4d %20s %20s %6.1fMB %s (%s)" % (idx,
                                               ("%s:%s" % (backup.env_backup['site']['name'], backup.env_backup['name'])),
                                               ("%s:%s" % (backup.env_site['site']['name'], backup.env_site['name'])),
                                               backup.size / (1024 * 1024),
                                               backup.filename,
                                               backup.dt_create))

        print("Listed jobs: %d  Total size: %.1fMB" % (idx, total_size / (1024 * 1024)))


class BackupJob(namedtuple('BackupJob', 'env_backup env_site root filename dt_create size')):
    pass


class BackupManager():

    def __init__(self, st):
        self.st = st
        self.ctx = st.ctx

    def list_backups(self, match='::::'):

        # Walk backup

        (backup_site_name, backup_site_env, src_site_name, src_site_env, job_expr) = match.split(":")

        jobs = []

        for site_name, site in self.ctx['sites'].items():
            if backup_site_name in ('*', '') or backup_site_name == site_name:
                for env_name, env in site['envs'].items():
                    if ('backup_storage' in env and env['backup_storage']) and (backup_site_env in ('*', '') or backup_site_env == env_name):
                        res = self._list_backup_site(env, src_site_name, src_site_env, job_expr)
                        jobs.extend(res)

        jobs.sort(key=lambda x: x.dt_create)
        return jobs

    def _list_backup_site(self, env, src_site_name, src_site_env, job_expr):

        jobs = []

        for site_name_o, site_o in self.ctx['sites'].items():
            if src_site_name in ('*', '') or src_site_name == site_name_o:
                for env_name_o, env_o in site_o['envs'].items():
                    if ('backup_storage' not in env_o or not env_o['backup_storage']) and (src_site_env in ('*', '') or src_site_env == env_name_o):

                        #print("%s  %s %s" % (env, site_name_o, env_name_o))
                        res = self._list_backups(env, env_o, job_expr)
                        jobs.extend(res)

        return jobs

    def _list_backups(self, env, env_o, job_expr):

        src_site_name = env_o['site']['name']
        src_site_env = env_o['name']

        backup_path = '%s/%s' % (src_site_name, src_site_env)
        # FIXME: This hits backends (ie SSH) too much: list the entire backup site and then pick from results
        files = env['files'].file_list(backup_path)

        jobs = []

        for f in files:
            jobs.append(BackupJob(env, env_o, f[0], f[1], f[3], f[2]))

        jobs.sort(key=lambda x: x.dt_create)

        if job_expr.startswith('-'):
            jobs = jobs[- int(job_expr[1:])]
            jobs = [jobs]

        return jobs

