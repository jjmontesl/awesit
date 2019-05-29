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


class SiteFile(namedtuple('SiteFile', 'relpath size mtime')):

    '''
    def __str__(self):
        return ("%s:%s:%s:%s:%s" % (self.env_backup['site']['name'],
                                    self.env_backup['name'],
                                    self.env_site['site']['name'],
                                    self.env_site['name'],
                                    self.index))
    '''
    pass



class FilesDiffCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Show differences between two sites file trees'

    def __init__(self, sitetool):
        self.st = sitetool

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("enva", help="site:env - site and environment A")
        parser.add_argument("envb", help="site:env - target backup site and environment")
        parser.add_argument("-t", "--ignore-time", action="store_true", default=False, help="ignore modification times")

        args = parser.parse_args(args)

        self.site_a = args.enva
        self.site_b = args.envb
        self.ignore_time = args.ignore_time

    def run(self):
        """
        """

        self.ctx = self.st.config

        dt_start = datetime.datetime.utcnow()

        # FIXME: This way of comparing (text-based) is incorrect regarding
        # directory differences

        logger.debug("Directory differences: %s - %s", self.site_a, self.site_b)

        (site_a_name, site_a_env) = Site.parse_site_env(self.site_a)
        (site_b_name, site_b_env) = Site.parse_site_env(self.site_b)

        backup_date = datetime.datetime.now()
        backup_job_name = backup_date.strftime('%Y%m%d-%H%M%S')

        site_a = self.ctx['sites'][site_a_name]['envs'][site_a_env]
        site_b = self.ctx['sites'][site_b_name]['envs'][site_b_env]

        # FIXME: This hits backends (ie SSH) too much: list the entire backup site and then pick from results

        files_a = site_a['files'].file_list('')
        files_b = site_b['files'].file_list('')

        files_a.sort(key=lambda f: f.relpath)
        files_b.sort(key=lambda f: f.relpath)

        if self.ignore_time:
            files_a_txt = ["%s %s" % (f.relpath, f.size) for f in files_a]
            files_b_txt = ["%s %s" % (f.relpath, f.size) for f in files_b]
        else:
            files_a_txt = ["%s %s %s" % (f.relpath, f.size, f.mtime) for f in files_a]
            files_b_txt = ["%s %s %s" % (f.relpath, f.size, f.mtime) for f in files_b]

        diff = list(difflib.unified_diff(files_a_txt, files_b_txt, n=0))

        if len(diff) > 0:
            print("\n".join(diff))
            #print (files_b_txt)

        print("Site A: %d files  Site B: %d files  (%d changes)" % (len(files_a), len(files_b), len(diff)))


