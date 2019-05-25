import argparse
import requests
import webbrowser
import yaml

import humanize


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
        files = site['files'].file_list('')
        count = 0
        size = 0
        last_date = 0
        for file in files:
            count += 1
            size += file[2]
            last_date = file[3] if not last_date or file[3] > last_date else last_date

        return {'count': count, 'size': size, 'dt_modification': last_date}


class SitesListCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool
        self.src = None
        self.info = False
        self.files = False
        self.backups = False

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool sites", description='Show configured sites and environments')
        parser.add_argument("source", default="*:*", nargs='?', help="site:env - site environment filter")
        parser.add_argument("-i", "--info", action="store_true", default=False, help="show site configuration info")
        parser.add_argument("-f", "--files", action="store_true", default=False, help="calculate site files size")
        parser.add_argument("-b", "--backups", action="store", type=str, nargs='?', const="*:main", default=None, help="show backups information (optionally use a filter *:*)")

        args = parser.parse_args(args)

        self.src = args.source
        self.files = args.files
        self.backups = args.backups
        self.info = args.info

        if self.backups == '':
            self.backups = False

    def run(self):
        """
        """

        self.ctx = self.st.config

        sites = self.st.sites.list_sites(self.src)

        # add backup info if needed
        backups = {}
        if self.backups:
            backupmanager = self.st.backupmanager
            jobs = backupmanager.list_backups(self.backups + ':' + self.src + ':*')
            jobs = backupmanager.group_backups(jobs)
            for job in jobs:
                key = (job.env_site['site']['name'], job.env_site['name'])
                backups[key] = job

        count = 0
        for site in sites:
            count += 1
            key = (site['site']['name'], site['name'])
            backup = backups.get(key, None)

            if self.files:
                size_data = self.st.sites.calculate_site_size(site)
                print("%-20s [%7.1fM / %5s files] (%s) %s" %
                      (("%s:%s" % (site['site']['name'], site['name'])),
                       size_data['size'] / (1024 * 1024) if size_data else 0,
                       size_data['count'] if size_data else 0,
                       humanize.naturaltime(size_data['dt_modification']) if size_data and size_data['dt_modification'] else '-',
                       site['files'].path))
            # TODO: Allow options together
            elif self.backups:
                print("%-20s [%6.1fM / %3s backups] %s" %
                      (("%s:%s" % (site['site']['name'], site['name'])),
                       backup.size / (1024 * 1024) if backup else 0,
                       backup.count if backup else 0,
                       site['url'] if 'url' in site else '-'))
            else:
                print("%-20s %s" % (("%s:%s" % (site['site']['name'], site['name'])),
                                    site['url'] if 'url' in site else '-'))

            if self.info:
                if 'db' in site:
                    print("  - db:    %s (%s)" % (site['db'].db, site['db'].__class__.__name__))
                print("  - files: %s (%s)" % (site['files'].path, site['files'].__class__.__name__))
                if 'git' in site:
                    print("  - git:   branch '%s'" % (site['git'].branch))
                print()

        print("Listed sites: %d" % (count))
