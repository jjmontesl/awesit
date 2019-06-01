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
from sitetool.core.util import timeago, bcolors
import difflib
import fabric
import csv
import tempfile

logger = logging.getLogger(__name__)


class DataFilesExportCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Export data to a structure of files that can be edited'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("site", help="site:env - site to export")
        #parser.add_argument("target", help="site:env|path - site or dir to export to")
        #parser.add_argument("profile", help="data profile to use")

        args = parser.parse_args(args)

        self.site = args.site

    def run(self):
        """
        """

        dt_start = datetime.datetime.utcnow()

        settings = self.ctx.get('settings')
        profiles = settings.setting('data.profiles')
        profile = profiles['joomla']

        (site_name, site_env) = Site.parse_site_env(self.site)
        site = self.ctx.get('sites').site_env(site_name, site_env)
        db = site.comp('db')

        logger.debug("Data export: %s", db.get_name())
        db_serialized = db.serialize()

        local_path = tempfile.mktemp(prefix='sitetool-tmp-export-')
        logger.debug("Writing files to: %s", local_path)

        for item in profile:

            table_name = item['table']
            table = db_serialized[table_name]

            table_path = os.path.join(local_path, table_name)
            os.makedirs(table_path)

            logger.info("Exporting '%s' to: %s", table_name, table_path)
            # Walk rows
            for row in table:
                data = self.export_row(profile, table, row)
                key = row[0]
                with open(os.path.join(table_path, key + ".data"), "w") as f:
                    f.write(data)

    def export_row(self, profile, table, row):
        text = ""
        for field in row:
            text  = text + field + "\n"
        return text

