# SiteTool

import argparse
import logging
import datetime

from sitetool.sites import Site
import webbrowser
import sys

logger = logging.getLogger(__name__)


class BrowserCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Opens a browser tab pointing to a site'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("target", help="site:env - target site and environment")

        args = parser.parse_args(args)

        self.target = args.target

    def run(self):
        """
        A backup copies different items (files, databases...) and generates
        a single "archived artifact" for each.
        """

        #(src_site_name, src_site_env) = Site.parse_site_env(self.target)
        #site = self.ctx.get('sites').site_env(src_site_name, src_site_env)

        sites = self.ctx.get('sites').list_sites(self.target)
        for site in sites:
            if site.url:
                logger.info("Opening browser for '%s': %s", self.target, site.url)
                webbrowser.open_new_tab(site.url)
            else:
                logger.warn("No URL defined for site '%s'", site.selector)
                #sys.exit(1)

