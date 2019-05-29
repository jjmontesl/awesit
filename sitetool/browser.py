# SiteTool

import argparse
import logging
import datetime

from sitetool.sites import Site
import webbrowser

logger = logging.getLogger(__name__)


class BrowserCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Opens a browser tab pointing to a site'

    def __init__(self, sitetool):
        self.st = sitetool

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

        self.ctx = self.st.config

        (src_site_name, src_site_env) = Site.parse_site_env(self.target)
        site = self.ctx['sites'][src_site_name]['envs'][src_site_env]

        url = site['url']

        logger.info("Opening browser for [%s]: %s", self.target, url)
        webbrowser.open_new_tab(url)

