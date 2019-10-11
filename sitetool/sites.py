import argparse
import requests
import webbrowser
import yaml

import humanize

from sitetool.core.util import timeago
from sitetool.core.components import SiteToolComponent, SiteComponent, SiteToolSettings
import logging
import sys


logger = logging.getLogger(__name__)


class Site(SiteToolComponent):
    '''
    '''

    def __init__(self, ctx, config):
        super().__init__(ctx)
        self.config = config
        self.envs = self.config['envs']
        self.name = self.config['name']

    def initialize(self, ctx):

        self.ctx = ctx
        for env_name, env_config in self.envs.items():
            env_config['name'] = env_name
            env_config['site'] = self
            site = SiteEnv(ctx, env_config, self)
            self.config['envs'][env_name] = site
            site.initialize(ctx)

    @staticmethod
    def parse_site_env(value):
        try:
            (site, env) = value.strip().split(':')
        except ValueError as e:
            logger.error("Invalid site definition '%s' (expecting <site>:<env>)." % value)
            sys.exit(1)
        return (site, env)

    def env(self, env_name):
        if env_name not in self.envs:
            logger.error("Site '%s' contains no environment named '%s'.", self.name, env_name)
            sys.exit(1)
        site = self.envs[env_name]
        return site

    def setting(self, setting, type):
        """
        Evaluates a setting value by combining current value with environment,
        site and global settings.
        """
        # Get settings
        base_value = self.ctx.get('settings').setting(setting)
        my_value = self.config.get('settings').get(setting) if 'settings' in self.config else None
        result = SiteToolSettings.combine(base_value, my_value, type)
        #logger.info("(S) Setting: %s  Type: %s  My Value: %s  (Base Value: %s): %s", setting, type, my_value, base_value, result)
        return result


class SiteEnv(SiteToolComponent):

    def __init__(self, ctx, config, site):
        super().__init__(ctx)
        self.config = config
        self.name = self.config['name']
        self.site = site

        self.url = self.config.get('url', None)
        self.selector = "%s:%s" % (self.site.name, self.name)

    def key(self):
        return (self.site.name, self.name)

    def __str__(self):
        return self.selector

    def initialize(self, ctx):
        self.ctx = ctx
        for comp_name, comp in self.config.items():
            if not isinstance(comp, SiteComponent):
                continue
            try:
                comp.initialize(ctx, self)
            except Exception as e:
                logger.error("Cannot initialize site component %s (%s): %s", comp_name, comp, e)
                raise

    def comp(self, name):
        return self.config.get(name, None)

    def setting(self, setting, type):
        """
        Evaluates a setting value by combining current value with environment,
        site and global settings.
        """
        # Get settings
        base_value = self.site.setting(setting, type)
        my_value = self.config.get('settings').setting(setting) if 'settings' in self.config else None
        result = SiteToolSettings.combine(base_value, my_value, type)
        #logger.info("(E) Setting: %s  Type: %s  My Value: %s  (Base Value: %s): %s", setting, type, my_value, base_value, result)
        return result


class SiteManager(SiteToolComponent):
    '''
    '''

    def __init__(self, ctx, config):
        super().__init__(ctx)
        self.config = config
        self.sites = None

        for site_name, siteconfig in self.config.items():
            siteconfig['name'] = site_name
            self.config[site_name] = Site(ctx, siteconfig)

    def initialize(self, ctx):
        for site_name, site in self.config.items():
            site.initialize(ctx)
        self.sites = self.config

    def get_site(self, selector):
        site_name, env_name = selector.split(":")
        site = self.site_env(site_name, env_name)
        return site

    def site_env(self, site_name, env_name):
        if site_name not in self.sites:
            logger.error("Invalid site name '%s'." % site_name)
            sys.exit(1)
        site = self.sites[site_name].env(env_name)
        return site

    def list_sites(self, match=':'):

        (match_site, match_env) = Site.parse_site_env(match)

        sites = []
        for site_name, site in self.sites.items():
            if match_site in ('*', '') or match_site == site_name:
                for env_name, env in site.envs.items():
                    if (match_env in ('*', '') or match_env == env_name):
                        sites.append(env)

        sites.sort(key=lambda x: (x.site.name, x.name))

        return sites

    def calculate_site_size(self, site):

        count = 0
        size = 0
        last_date = 0

        if 'files' in site.config:
            files, errors = site.comp('files').file_list('')
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

    def __init__(self, ctx):
        self.ctx = ctx
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

        sites = self.ctx.get('sites').list_sites(self.src)

        # add backup info if needed
        backups = {}
        if self.backups:
            backupmanager = self.ctx.get('backups')
            jobs = backupmanager.list_backups(self.backup_sites + ':' + self.src + ':*')
            jobs = backupmanager.group_backups(jobs)
            for job in jobs:
                key = job.env_site.key()
                backups[key] = job

        count = 0
        for site in sorted(sites, key=lambda x: (x.site.name, x.name)):
            count += 1
            key = site.key()
            backup = backups.get(key, None)

            label = site.url or '-'

            backups_info_text = ''
            files_info_text = ''

            if self.backups:
                backups_info_text = ('[%6.1fM / %3s backups - %15s] ' % (
                                     backup.size / (1024 * 1024) if backup else 0,
                                     backup.count if backup else 0,
                                     timeago(backup.dt_create) if backup else '-'))

            if self.files:
                size_data = self.ctx.get('sites').calculate_site_size(site)
                files_info_text = ('[%7.1fM / %5s files - %15s] ' % (
                                   size_data['size'] / (1024 * 1024) if size_data else 0,
                                   size_data['count'] if size_data else 0,
                                   timeago(size_data['dt_modification']) if size_data and size_data['dt_modification'] else '-'))
                label = site.comp('files').path if 'files' in site.config else label

            print("%-26s %s%s %s" % (site.selector,
                                     files_info_text,
                                     backups_info_text,
                                     label))

            if self.verbose:
                if 'db' in site.config:
                    print("  db:    %s (%s)" % (getattr(site.comp('db'), 'db', ""), site.comp('db').__class__.__name__))
                if 'files' in site.config:
                    print("  files: %s (%s)" % (site.comp('files').path, site.comp('files').__class__.__name__))
                if 'git' in site.config:
                    print("  git:   branch '%s'" % (site.comp('git').branch))
                print()

        print("Listed sites: %d" % (count))
