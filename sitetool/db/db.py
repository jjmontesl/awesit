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
import difflib


logger = logging.getLogger(__name__)


class DatabaseSerializeCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Dump database tables into serialized format usable to calculate differences.'

    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("site", help="site:env - site to serialize")

        args = parser.parse_args(args)

        self.site = args.site

    def run(self):
        """
        """

        self.ctx = self.st.config

        dt_start = datetime.datetime.utcnow()

        (site_name, site_env) = Site.parse_site_env(self.site)
        site = self.ctx['sites'][site_name]['envs'][site_env]
        db = site['db']

        logger.debug("Database serialization: %s", db.get_name())

        db_serialized = db.serialize()

        print(db_serialized)


class DatabaseDiffCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Compare data in two databases with same schema.'

    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("enva", help="site:env - site and environment A")
        parser.add_argument("envb", help="site:env - target backup site and environment")

        args = parser.parse_args(args)

        self.site_a = args.enva
        self.site_b = args.envb

    def run(self):
        """
        """

        self.ctx = self.st.config

        dt_start = datetime.datetime.utcnow()

        logger.debug("DB differences: %s - %s", self.site_a, self.site_b)

        (site_a_name, site_a_env) = Site.parse_site_env(self.site_a)
        (site_b_name, site_b_env) = Site.parse_site_env(self.site_b)

        backup_date = datetime.datetime.now()
        backup_job_name = backup_date.strftime('%Y%m%d-%H%M%S')

        site_a = self.ctx['sites'][site_a_name]['envs'][site_a_env]
        site_b = self.ctx['sites'][site_b_name]['envs'][site_b_env]

        db_a = site_a['db']
        db_b = site_b['db']

        logger.debug("Serializing databases")

        # TODO: Allow usage of files if serialized versions are stored
        db_a_serialized = db_a.serialize()
        db_b_serialized = db_b.serialize()

        logger.debug("Calculating data differences")
        tables_a = set(db_a_serialized.keys())
        tables_b = set(db_b_serialized.keys())

        tables_added = tables_a - tables_b
        print("Tables > (%d): %s" % (len(tables_added), tables_added if tables_added else "None"))

        tables_removed = tables_b - tables_a
        print("Tables removed (%d): %s" % (len(tables_removed), tables_removed if tables_removed else "None"))

        # Differences in rows in common tables
        print("Table Changes:")
        for table in sorted(list(tables_a & tables_b)):
            rows_a = set([tuple(r) for r in db_a_serialized[table]])
            rows_b = set([tuple(r) for r in db_b_serialized[table]])
            rows_added = sorted(list(rows_a - rows_b))
            rows_removed = sorted(list(rows_b - rows_a))

            if rows_added or rows_removed:

                print("%s (added: %d, removed: %d)" % (table, len(rows_added), len(rows_removed)))
                if True:
                    lines = []
                    for row in rows_added:
                        lines.append("+ %s" % (",".join(row)))
                    for row in rows_removed:
                        lines.append("- %s" % (",".join(row)))

                    sorted_lines = sorted(lines, key=lambda l: (l[2:], l[0]))

                    print("\n".join(sorted_lines))

        #tables_diff = ItemDiff(name, added/removed/changed, )


