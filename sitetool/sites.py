import argparse
import requests
import webbrowser
import yaml


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


class SitesListCommand():
    '''
    '''
    def __init__(self, sitetool):
        self.st = sitetool
        self.src = None
        self.size = False
        self.backups = False

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool sites", description='Show configured sites and environments')
        parser.add_argument("source", default="*:*", nargs='?', help="site:env - site environment filter")
        #parser.add_argument("-s", "--size", action="store_true", default=False, help="calculate site files size")
        parser.add_argument("-b", "--backups", action="store", type=str, nargs='?', const="*:default", default=None, help="show backups information (optionally use a filter *:*)")

        args = parser.parse_args(args)

        self.src = args.source
        #self.size = args.size
        self.backups = args.backups

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

            if self.backups:
                print("%-20s [%6.1fM / %3s backups] %s" %
                      (("%s:%s" % (site['site']['name'], site['name'])),
                                   backup.size / (1024 * 1024) if backup else 0,
                                   backup.count if backup else 0,
                                   site['url'] if 'url' in site else '-'))
            else:
                print("%-20s %s" % (("%s:%s" % (site['site']['name'], site['name'])),
                                    site['url'] if 'url' in site else '-'))

        print("Listed sites: %d" % (count))
