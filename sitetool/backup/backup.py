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
from sitetool.core.util import timeago
from sitetool.core.components import SiteToolComponent, SiteToolSettings
from sitetool.core.exceptions import SiteToolException
import json

logger = logging.getLogger(__name__)


class BackupJobRenameOtherToBackupJobItem():   # Backup Item

    def __init__(self):

        self.env_backup = env_backup
        self.env_site = env_site

        self.hash = None

        self.itemnames = None  # ['files', 'db']
        self.items = None  # BackupJobItems

        self.tags = None

        self.index = None  # only if in a listing

    def __str__(self):
        return ("%s:%s:%s:%s:%s" % (self.env_backup.site.name,
                                    self.env_backup.name,
                                    self.env_site.site.name,
                                    self.env_site.name,
                                    self.index))


class BackupJob():  # namedtuple('BackupJob', 'env_backup env_site relpath dt_create size index count')):

    def __init__(self, item, env_backup, env_site, relpath, dt_create, size, file_count, errors_count):
        self.relpath = relpath
        self.dt_create = dt_create
        self.size = size
        self.file_count = file_count
        self.errors_count = errors_count

        self.item = item  # 'files'

    def __str__(self):
        return ("%s:%s:%s:%s:%s" % (self.env_backup.site.name,
                                    self.env_backup.name,
                                    self.env_site.site.name,
                                    self.env_site.name,
                                    self.index))

    def serialize(self):
        data = self.__dict__
        return json.dumps(data)

    def deserialize(self, data):
        datadict = json.loads(data)
        self.__dict__.update(datadict)


class BackupCommand():
    '''
    Perform a files backup from a given site.
    '''

    COMMAND_DESCRIPTION = 'Backup a given site'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("src", help="site:env - source site and environment")
        parser.add_argument("dst", nargs='?', default=None, help="site:env - target backup site and environment")
        parser.add_argument("-i", "--item", default=None, type=str, help="backup given items only (separate multiple items with commas: files,db)")
        parser.add_argument("-t", "--tag", default=None, type=str, help="tag backup (separate multiple tags with commas)")

        args = parser.parse_args(args)

        self.src = args.src
        self.dst = args.dst

    def run(self):
        """
        A backup copies different items (files, databases...) and generates
        a single "archived artifact" for each.
        """

        dt_start = datetime.datetime.utcnow()

        if not self.dst:
            self.dst = 'backup:main' #default_backup_dst

        src_site = self.ctx.get('sites').get_site(self.src)
        backup_site = self.ctx.get('sites').get_site(self.dst)

        backupmanager = self.ctx.get('backups')
        #backups = backupmanager.list_backups(self.src)
        job = backupmanager.backup(src_site, backup_site)

        backup_time = (datetime.datetime.utcnow() - dt_start).total_seconds()
        logger.info("Backup finished (time: %.1fm, size=%.2fM)", backup_time / 60.0, job.size / (1024 * 1024))


class BackupDeleteCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Delete backup jobs data'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool backup-delete", description=self.COMMAND_DESCRIPTION)
        parser.add_argument("backup", default=None, help="backupsite:env:site:env:sel - backup(s) to delete")
        parser.add_argument("-l", "--list", action="store_true", default=False, help="list backups that would be deleted and exit")
        parser.add_argument("-y", "--yes", action="store_true", default=False, help="allow deleting more than one backup")

        args = parser.parse_args(args)

        self.src = args.backup
        self.yes = args.yes
        self.list = args.list

    def run(self):
        """
        """

        backupmanager = self.ctx.get('backups')
        backups = backupmanager.list_backups(self.src)

        if len(backups) == 0:
            logger.error("No backups matched your filter: '%s'", self.src)
            sys.exit(1)

        logger.info("Backups selected:")
        command = BackupListCommand(self.ctx)
        command.src = self.src
        command.run()

        if self.list:
            sys.exit(0)

        # Confirm
        if not self.yes:
            confirm = input("Are you sure you want to delete %d backups? [y/N] " % len(backups))
            if confirm.lower() not in ('y', 'yes'):
                logger.info("Cancelled by user")
                sys.exit(0)

        logger.info("Deleting %d backups.", len(backups))

        for job in backups:

            backup_site = job.env_backup
            src_site = job.env_site

            logger.info("Deleting backup: %s", job)
            job_filename = os.path.basename(job.relpath)

            # Copy and restore files
            backup_path = '%s/%s/%s' % (src_site.site.name, src_site.name, job_filename)
            backup_site.comp('files').file_delete(backup_path)


class BackupTagCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Tag or untag backups'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool backup-tag", description=self.COMMAND_DESCRIPTION)
        parser.add_argument("backup", default=None, help="backupsite:env:site:env:sel - backup(s) to delete")
        parser.add_argument("-l", "--list", action="store_true", default=False, help="list backups that would be deleted and exit")
        parser.add_argument("-t", "--tag", default=None, type=str, help="tag backup (separate multiple tags with commas)")
        parser.add_argument("-u", "--untag", default=None, type=str, help="remove tag(s) (separate multiple tags with commas)")

        args = parser.parse_args(args)

        self.src = args.backup

        # FIXME: Validate: tags cannot start with '-'
        self.tag = args.tag.split(",")
        self.untag = args.untag.split(",")

    def run(self):
        """
        """

        backupmanager = self.ctx.get('backups')
        backups = backupmanager.list_backups(self.src)

        if len(backups) == 0:
            logger.error("No backups matched your filter: '%s'", self.src)
            sys.exit(1)

        logger.info("Backups selected:")
        command = BackupListCommand(self.ctx)
        command.src = self.src
        command.run()

        if self.list:
            sys.exit(0)

        # Confirm
        if not self.yes:
            confirm = input("Are you sure you want to tag %d backups? [y/N] " % len(backups))
            if confirm.lower() not in ('y', 'yes'):
                logger.info("Cancelled by user")
                sys.exit(0)

        logger.info("Tagging %d backups.", len(backups))

        for job in backups:
            '''
            backup_site = job.env_backup
            src_site = job.env_site

            logger.info("Deleting backup: %s", job)
            job_filename = os.path.basename(job.relpath)

            # Copy and restore files
            backup_path = '%s/%s/%s' % (src_site.site.name, src_site.name, job_filename)
            backup_site.comp('files').file_delete(backup_path)
            '''
            raise NotImplementedError()



class BackupListCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Show available backup jobs'

    def __init__(self, ctx):
        self.ctx = ctx
        self.src = None
        self.by_size = False
        self.reverse = False
        self.exact_time = False
        self.aggregate = False

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool backup-list", description=self.COMMAND_DESCRIPTION)
        parser.add_argument("source", default=None, nargs='?', help="backupsite:env:site:env:sel - source backup and site environments")
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

        backupmanager = self.ctx.get('backups')
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
            print("%20s %20s %5d %7.1fM %s (%s)" % (
                backup.env_backup.selector if backup.env_backup else '-',
                backup.env_site.selector if backup.env_site else '-',
                backup.index if backup.index is not None else backup.count,
                backup.size / (1024 * 1024),
                os.path.basename(backup.relpath) if backup.relpath else '-',
                backup.dt_create if self.exact_time else timeago(backup.dt_create)))

        print("Listed jobs: %d  Total size: %.1fMB" % (count, total_size / (1024 * 1024)))


class BackupManager(SiteToolComponent):

    def __init__(self, ctx):
        self.ctx = ctx

    def initialize(self, ctx):
        self.ctx = ctx

    def backup(self, src_site, backup_site):

        backup_date = datetime.datetime.utcnow()

        logger.info("Backup %s to %s", src_site, backup_site)

        # TODO: Objects should define their backup artifacts (from 0 to N)
        backup_size = 0

        # Copy files
        if 'files' in src_site.config:
            backup_size += self._backup_files(src_site, backup_site, backup_date)
        # Copy database
        if 'db' in src_site.config:
            backup_size += self._backup_database(src_site, backup_site, backup_date)

        # TODO: return backup job
        job = BackupJob(backup_site, src_site, '', backup_date, backup_size, None, None)
        return job

    def _backup_files(self, src_site, backup_site, backup_date):

        logger.debug("Backup files for: %s", src_site)
        backup_job_name = backup_date.strftime('%Y%m%d-%H%M%S')

        (tmpfile_path, files_hash) = src_site.comp('files').archive()
        #logger.info("Backup remote file path: %s (hash: %x)", files_path, files_hash or 0)

        stats = os.stat(tmpfile_path)
        backup_size = stats[stat.ST_SIZE]

        # Copy backup file to place
        #backup_root_dir = '/home/jjmontes/sitetool/backup/'
        backup_path = '%s/%s/%s-%s-%s-files.tar.gz' % (src_site.site.name, src_site.name, src_site.site.name, src_site.name, backup_job_name)

        backup_site.comp('files').file_put(tmpfile_path, backup_path)

        os.unlink(tmpfile_path)

        job = BackupJob(backup_site, src_site, '', backup_date, backup_size, None, None)

        return backup_size

    def _backup_database(self, src_site, backup_site, backup_date):

        logger.info("Backup DB for: %s", src_site)
        backup_job_name = backup_date.strftime('%Y%m%d-%H%M%S')

        (tmpdb_path, tmpdb_hash) = src_site.comp('db').dump()
        logger.debug("Backup DB result path: %s", tmpdb_path)

        stats = os.stat(tmpdb_path)
        backup_size = stats[stat.ST_SIZE]

        # Copy database file to place
        #backup_root_dir = '/home/jjmontes/sitetool/backup/'
        backup_path = '%s/%s/%s-%s-%s-db.tar.gz' % (src_site.site.name, src_site.name, src_site.site.name, src_site.name, backup_job_name)

        backup_site.comp('files').file_put(tmpdb_path, backup_path)

        os.unlink(tmpdb_path)

        return backup_size

    def parse_backup_selector(self, selector):

        backup_selector = self.setting('backup.selector', 'replace', '*:*')

        backup_site_name = backup_selector.split(":")[0]
        backup_site_env = backup_selector.split(":")[1]

        src_site_name = ""
        src_site_env = ""

        job_expr = ""

        parts = selector.split(":") if selector else []
        if len(parts) == 0:
            return (backup_site_name, backup_site_env, src_site_name, src_site_env, job_expr)
        elif len(parts) == 1:
            # Site name
            return (backup_site_name, backup_site_env, parts[0], src_site_env, job_expr)
        elif len(parts) == 2:
            # Site and env name
            return (backup_site_name, backup_site_env, parts[0], parts[1], job_expr)
        elif len(parts) == 3:
            # Site and env name
            return (backup_site_name, backup_site_env, parts[0], parts[1], parts[2])
        elif len(parts) == 4:
            # Site and env name
            return (parts[0], parts[1], parts[2], parts[3], job_expr)
        elif len(parts) == 5:
            return (parts[0], parts[1], parts[2], parts[3], parts[4])
        else:
            raise SiteToolException("Invalid backup selector: '%s'" % selector)


    def group_backups(self, backups):
        groups = defaultdict(lambda: {'count': 0, 'size': 0, 'dt_create': None})
        for job in backups:
            key = job.env_site.key()
            group = groups[key]
            group['env_site'] = job.env_site
            group['count'] += 1
            group['size'] += job.size
            group['dt_create'] = job.dt_create if not group['dt_create'] or job.dt_create > group['dt_create'] else group['dt_create']

        jobs = []
        for key, group in groups.items():
            jobs.append(BackupJob(None, group['env_site'], None, group['dt_create'], group['size'], None, group['count']))

        return jobs

    def list_backups(self, match=None):

        # TODO: Separate method
        (backup_site_name, backup_site_env, src_site_name, src_site_env, job_expr) = self.parse_backup_selector(match)

        jobs = []

        # Walk backups
        for site_name, site in self.ctx.get('sites').sites.items():
            if backup_site_name in ('*', '') or backup_site_name == site_name:
                for env_name, env in site.envs.items():
                    if (env.config.get('backup_storage', False) and (backup_site_env in ('*', '') or backup_site_env == env_name)):
                        res = self._list_backup_site(env, src_site_name, src_site_env, job_expr)
                        jobs.extend(res)

        jobs.sort(key=lambda x: x.dt_create)
        return jobs

    def _list_backup_site(self, env, src_site_name, src_site_env, job_expr):

        jobs = []

        for site_name_o, site_o in self.ctx.get('sites').sites.items():
            if src_site_name in ('*', '') or src_site_name == site_name_o:
                for env_name_o, env_o in site_o.envs.items():
                    if (not env_o.config.get('backup_storage', False)) and (src_site_env in ('*', '') or src_site_env == env_name_o):
                        #print("%s  %s %s" % (env, site_name_o, env_name_o))
                        res = self._list_backups(env, env_o, job_expr)
                        jobs.extend(res)

        return jobs

    def _list_backups(self, env, env_o, job_expr):

        src_site_name = env_o.site.name
        src_site_env = env_o.name

        # Obtain file list from files
        backup_path = '%s/%s' % (src_site_name, src_site_env)
        # FIXME: This hits backends (ie SSH) too much: list the entire backup site and then pick from results
        files, errors = env.comp('files').file_list(backup_path)

        jobs = []

        files.sort(key=lambda f: f.mtime)
        files.reverse()
        idx = 0
        for f in files:
            idx += 1
            jobs.append(BackupJob(env, env_o, f.relpath, f.mtime, f.size, idx, 1))

        jobs.sort(key=lambda x: x.dt_create)
        for job in jobs:
            job

        if job_expr and jobs and job_expr != '*':
            if '-' in job_expr:
                # Range
                range_a = job_expr.split("-")[0]
                range_b = job_expr.split("-")[1]

                idx_a = int(range_a) if range_a else None
                idx_b = int(range_b) if range_b else None

                if idx_a and idx_b:
                    if int(idx_b) < int(idx_a):
                        (idx_a, idx_b) = (idx_b, idx_a)

                    # Ranges ending in 0 ([-3:0]) are invalid
                    if -int(idx_a) + 1 == 0:
                        jobs = jobs[-int(idx_b) :]
                    else:
                        jobs = jobs[-int(idx_b) : -int(idx_a) + 1]

                elif idx_a:
                    jobs = jobs[:-int(idx_a) + 1]
                else:
                    jobs = jobs[-int(idx_b):]
            else:
                # Single index
                idx = int(job_expr)

                if (idx <= len(jobs)):
                    jobs = [jobs[-idx]]
                else:
                    jobs = []

        return jobs

