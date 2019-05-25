# SiteTool

from collections import defaultdict
from collections import namedtuple
import argparse
import datetime
import hashlib
import logging
import os
import stat
import sys

from sitetool.sites import Site
import humanize


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

        logger.info("Backup finished (time: %.1fm, size=%.2fM)", backup_time / 60.0, backup_size / (1024 * 1024))

    def _backup_database(self, src_site):

        db_path = src_site['db'].dump()
        logger.info("Backup db path: %s", db_path)

        # Copy database file to place


class BackupDeleteCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool backup-delete", description='Delete backup jobs data (use with caution!)')
        parser.add_argument("backup", default=None, help="backupsite:env:site:env:sel - backup(s) to delete")
        parser.add_argument("-m", "--many", action="store_true", default=False, help="allow deleting more than one backup")
        parser.add_argument("-l", "--list", action="store_true", default=False, help="list backups that would be deleted and exit")

        args = parser.parse_args(args)

        self.src = args.backup
        self.many = args.many
        self.list = args.list

    def run(self):
        """
        """

        if self.list:
            logger.info("Listing backups that would be deleted by this filter:")
            command = BackupListCommand(self.st)
            command.src = self.src
            return command.run()

        self.ctx = self.st.config
        backupmanager = BackupManager(self.st)
        backups = backupmanager.list_backups(self.src)

        if len(backups) == 0 and not self.many:
            logger.error("No backups matched your filter %s", self.src)
            sys.exit(1)
        elif len(backups) > 1 and not self.many:
            logger.error("Cannot delete backups: %d backups matched your filter %s (use -l to list, --many if you want to delete all of them)", len(backups), self.src)
            sys.exit(1)

        logger.info("Deleting %d backups.", len(backups))

        for job in backups:

            backup_site = job.env_backup
            src_site = job.env_site

            logger.info("Deleting backup: %s", job)

            # Copy and restore files
            backup_path = '%s/%s/%s' % (src_site['site']['name'], src_site['name'], job.filename)
            backup_site['files'].file_delete(backup_path)


class BackupListCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool
        self.src = None
        self.by_size = False
        self.reverse = False
        self.exact_time = False
        self.aggregate = False

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool backup-list", description='Show available backup jobs')
        parser.add_argument("source", default="::::", nargs='?', help="backupsite:env:site:env - source backup and site environments")
        parser.add_argument("-s", "--by-size", action="store_true", default=False, help="sort by size")
        parser.add_argument("-r", "--reverse", action="store_true", default=False, help="reverse ordering")
        parser.add_argument("-t", "--time", action="store_true", default=False, help="show exact datetimes")
        parser.add_argument("-a", "--aggregate", action="store_true", default=False, help="aggregate results")

        args = parser.parse_args(args)

        self.src = args.source
        self.by_size = args.by_size
        self.reverse = args.reverse
        self.exact_time = args.time
        self.aggregate = args.aggregate

    def run(self):
        """
        """

        self.ctx = self.st.config
        backupmanager = BackupManager(self.st)
        backups = backupmanager.list_backups(self.src)

        if self.aggregate:
            backups = backupmanager.group_backups(backups)

        if self.by_size:
            backups.sort(key=lambda x: x.size)

        if self.reverse:
            backups.reverse()

        count = 0
        total_size = 0
        #md5 = hashlib.md5()
        for backup in backups:
            count += 1
            #md5.update(backup.env_backup['site']['name'].encode('utf-8'))
            #md5.update(backup.env_backup['name'].encode('utf-8'))
            #md5.update(backup.env_site['site']['name'].encode('utf-8'))
            #md5.update(backup.env_site['name'].encode('utf-8'))
            #md5.update(backup.filename.encode('utf-8'))
            total_size += backup.size
            print("%5d %20s %20s %6.1fMB %s (%s)" % (backup.index if backup.index is not None else backup.count,
                                                #md5.hexdigest()[:6],
                                               ("%s:%s" % (backup.env_backup['site']['name'], backup.env_backup['name'])) if backup.env_backup else '-',
                                               ("%s:%s" % (backup.env_site['site']['name'], backup.env_site['name'])),
                                               backup.size / (1024 * 1024),
                                               backup.filename or '-',
                                               backup.dt_create if self.exact_time else humanize.naturaltime(backup.dt_create)))

        print("Listed jobs: %d  Total size: %.1fMB" % (count, total_size / (1024 * 1024)))


class BackupJob(namedtuple('BackupJob', 'env_backup env_site root filename dt_create size index count')):

    def __str__(self):
        return ("%s:%s:%s:%s:%s" % (self.index,
                                    self.env_backup['site']['name'],
                                    self.env_backup['name'],
                                    self.env_site['site']['name'],
                                    self.env_site['name']))


class BackupManager():

    def __init__(self, st):
        self.st = st
        self.ctx = st.ctx

    def group_backups(self, backups):
        groups = defaultdict(lambda: {'count': 0, 'size': 0, 'dt_create': None})
        for job in backups:
            key = (job.env_site['site']['name'], job.env_site['name'])
            group = groups[key]
            group['env_site'] = job.env_site
            group['count'] += 1
            group['size'] += job.size
            group['dt_create'] = job.dt_create

        jobs = []
        for key, data in groups.items():
            jobs.append(BackupJob(None, data['env_site'], None, None, data['dt_create'], data['size'], None, data['count']))

        return jobs


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

        # Obtain file list from files
        backup_path = '%s/%s' % (src_site_name, src_site_env)
        # FIXME: This hits backends (ie SSH) too much: list the entire backup site and then pick from results
        files = env['files'].file_list(backup_path)

        jobs = []

        files.sort(key=lambda x: x[3])
        files.reverse()
        idx = 0
        for f in files:
            idx -= 1
            jobs.append(BackupJob(env, env_o, f[0], f[1], f[3], f[2], idx, 1))

        jobs.sort(key=lambda x: x.dt_create)
        for job in jobs:
            job

        if job_expr.startswith('-') and jobs:
            idx = int(job_expr)
            if (-idx <= len(jobs)):
                jobs = [jobs[idx]]
            else:
                jobs = []

        return jobs

