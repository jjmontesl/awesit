import argparse
import requests
import webbrowser
import yaml

import humanize

from sitetool.core.util import timeago


class Site():
    '''
    '''

    @staticmethod
    def parse_site_env(value):
        (site, env) = value.strip().split(':')
        return (site, env)


class SiteManager():
    '''
    '''

    def __init__(self, st):
        self.st = st
        self.ctx = self.st.config

    def list_sites(self, match=':'):

        # Walk backup

        (match_site, match_env) = Site.parse_site_env(match)

        sites = []
        for site_name, site in self.ctx['sites'].items():
            if match_site in ('*', '') or match_site == site_name:
                for env_name, env in site['envs'].items():
                    if (match_env in ('*', '') or match_env == env_name):
                        sites.append(env)

        sites.sort(key=lambda x: (x['site']['name'], x['name']))

        return sites

    def calculate_site_size(self, site):

        count = 0
        size = 0
        last_date = 0

        if 'files' in site:
            files = site['files'].file_list('')
            if files:
                for file in files:
                    count += 1
                    size += file.size
                    last_date = file.mtime if not last_date or file.mtime > last_date else last_date

        return {'count': count, 'size': size, 'dt_modification': last_date}


class SitesListCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Show configured sites and environments'

    def __init__(self, sitetool):
        self.st = sitetool
        self.src = None
        self.verbose = False
        self.files = False
        self.backups = False

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool sites", description=self.COMMAND_DESCRIPTION)
        parser.add_argument("source", default="*:*", nargs='?', help="site:env - site environment filter")
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show site configuration info")
        parser.add_argument("-f", "--files", action="store_true", default=False, help="calculate site files size")
        parser.add_argument("-b", "--backups", action="store_true", default=False, help="calculate site files size")
        parser.add_argument("--backup-sites", action="store", type=str, default="*:main", help="show backups information (optionally use a filter *:*)")

        args = parser.parse_args(args)

        self.src = args.source
        self.files = args.files
        self.backups = args.backups
        self.verbose = args.verbose

        self.backup_sites = args.backup_sites

    def run(self):
        """
        """

        self.ctx = self.st.config

        sites = self.st.sites.list_sites(self.src)

        # add backup info if needed
        backups = {}
        if self.backups:
            backupmanager = self.st.backupmanager
            jobs = backupmanager.list_backups(self.backup_sites + ':' + self.src + ':*')
            jobs = backupmanager.group_backups(jobs)
            for job in jobs:
                key = (job.env_site['site']['name'], job.env_site['name'])
                backups[key] = job

        count = 0
        for site in sorted(sites, key=lambda x: (x['site']['name'], x['name'])):
            count += 1
            key = (site['site']['name'], site['name'])
            backup = backups.get(key, None)

            label = site['url'] if 'url' in site else '-'

            backups_info_text = ''
            files_info_text = ''

            if self.backups:
                backups_info_text = ('[%6.1fM / %3s backups - %15s] ' % (
                                     backup.size / (1024 * 1024) if backup else 0,
                                     backup.count if backup else 0,
                                     timeago(backup.dt_create) if backup else '-'))

            if self.files:
                size_data = self.st.sites.calculate_site_size(site)
                files_info_text = ('[%7.1fM / %5s files - %15s] ' % (
                                   size_data['size'] / (1024 * 1024) if size_data else 0,
                                   size_data['count'] if size_data else 0,
                                   timeago(size_data['dt_modification']) if size_data and size_data['dt_modification'] else '-'))
                label = site['files'].path if 'files' in site else label

            print("%-20s %s%s %s" % (("%s:%s" % (site['site']['name'], site['name'])),
                                     files_info_text,
                                     backups_info_text,
                                     label))

            if self.verbose:
                if 'db' in site:
                    print("  db:    %s (%s)" % (getattr(site, 'db', ""), site['db'].__class__.__name__))
                if 'files' in site:
                    print("  files: %s (%s)" % (site['files'].path, site['files'].__class__.__name__))
                if 'git' in site:
                    print("  git:   branch '%s'" % (site['git'].branch))
                print()

        print("Listed sites: %d" % (count))
