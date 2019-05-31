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
from sitetool.core.components import SiteComponent
from sitetool.core.util import timeago
import difflib

import pathspec

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


class Files(SiteComponent):
    """
    Base objects for File connectors.

    Files backup format is a .tar.gz archive with paths relative to the site path.
    """

    path = None
    exclude = None

    '''
    def initialize(self):
        if self.path is None:
            raise SiteToolConfigException("No host set for SSHFiles: %s", self)
    '''

    def files_matches(self, relpaths, excludes):
        """
        Applies a file globbing pattern to a path.

        NOTE: pathspec seems to require paths to start with no leading slash,
        otherwise it fails to match general pattersn in the root dir.
        """
        matches = relpaths
        if excludes:
            spec = pathspec.PathSpec.from_lines('gitwildmatch', excludes)
            matches = spec.match_files(relpaths)  #([paths_rel[1:] ... ]):
        return matches

    def files_excluded(self, relpaths):
        """
        """
        excludes = self.setting('files.exclude', "array-extend", self.exclude)
        return self.files_matches(relpaths, excludes)

    def files_filtered(self, sitefiles):
        excluded = self.files_excluded([f.relpath for f in sitefiles])
        excluded_set = set(excluded)
        result = [f for f in sitefiles if f.relpath not in excluded_set]
        return result


class FilesListCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'List files in a site'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("site", help="site:env - site and environment")
        parser.add_argument("-s", "--by-size", action="store_true", default=False, help="sort by size")
        parser.add_argument("-t", "--by-time", action="store_true", default=False, help="sort by time")
        parser.add_argument("-r", "--reverse", action="store_true", default=False, help="reverse ordering")
        parser.add_argument("-a", "--all", action="store_true", default=False, help="show all files (excluded)")

        args = parser.parse_args(args)

        self.site = args.site
        self.by_size = args.by_size
        self.by_time = args.by_time
        self.reverse = args.reverse
        self.all = args.all

    def run(self):
        """
        """

        dt_start = datetime.datetime.utcnow()

        # FIXME: This way of comparing (text-based) is incorrect regarding
        # directory differences

        logger.debug("Directory listing: %s", self.site)

        (site_name, site_env) = Site.parse_site_env(self.site)
        site = self.ctx.get('sites').site_env(site_name, site_env)

        # FIXME: This hits backends (ie SSH) too much: list the entire backup site and then pick from results

        files = site.comp('files').file_list('', all=self.all)
        files.sort(key=lambda f: f.relpath)

        if self.by_size:
            files.sort(key=lambda x: x.size)
        if self.by_time:
            files.sort(key=lambda x: x.mtime)
        if self.reverse:
            files.reverse()

        # Print files
        total_size = 0
        for f in files:
            total_size += f.size
            print("%20s %10s %s" % (
                f.mtime,
                f.size,
                f.relpath))

        print(" %d files, %.1f MB" % (len(files), total_size / (1024 * 1024)))


class FilesDiffCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Show differences between two sites file trees'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("enva", help="site:env - site and environment A")
        parser.add_argument("envb", help="site:env - target backup site and environment")
        parser.add_argument("-t", "--ignore-time", action="store_true", default=False, help="ignore modification times")

        args = parser.parse_args(args)

        self.site_a = args.enva
        self.site_b = args.envb
        self.ignore_time = args.ignore_time

    def file_description(self, f):
        if self.ignore_time:
            file_txt = "%s %s" % (f.relpath, f.size)
        else:
            file_txt = "%s %s %s" % (f.relpath, f.size, f.mtime)
        return file_txt

    def run(self):
        """
        """

        dt_start = datetime.datetime.utcnow()

        # FIXME: This way of comparing (text-based) is incorrect regarding
        # directory differences

        logger.debug("Directory differences: %s - %s", self.site_a, self.site_b)

        (site_a_name, site_a_env) = Site.parse_site_env(self.site_a)
        (site_b_name, site_b_env) = Site.parse_site_env(self.site_b)

        backup_date = datetime.datetime.now()
        backup_job_name = backup_date.strftime('%Y%m%d-%H%M%S')

        site_a = self.ctx.get('sites').site_env(site_a_name, site_a_env)
        site_b = self.ctx.get('sites').site_env(site_b_name, site_b_env)

        # FIXME: This hits backends (ie SSH) too much: list the entire backup site and then pick from results

        files_a = site_a.comp('files').file_list('')
        files_b = site_b.comp('files').file_list('')

        if self.ignore_time:
            files_a = [("%s %s" % (f.relpath, f.size), f) for f in files_a]
            files_b = [("%s %s" % (f.relpath, f.size), f) for f in files_b]
        else:
            files_a = [("%s %s %s" % (f.relpath, f.size, f.mtime), f) for f in files_a]
            files_b = [("%s %s %s" % (f.relpath, f.size, f.mtime), f) for f in files_b]

        files_a_dict = {f[1].relpath: f for f in files_a}
        files_b_dict = {f[1].relpath: f for f in files_b}

        total_files_changed = 0
        total_files_added = 0
        total_files_deleted = 0
        files_a_set = set(files_a_dict.keys())
        files_b_set = set(files_b_dict.keys())

        # Print files
        files_added = sorted(list(files_a_set - files_b_set))
        files_removed = sorted(list(files_b_set - files_a_set))

        lines = []
        for f in files_added:
            total_files_added += 1
            lines.append("+%s" % files_a_dict[f][0])
        for f in files_removed:
            total_files_deleted += 1
            lines.append("-%s" % files_b_dict[f][0])

        for f in (files_a_set & files_b_set):
            if files_a_dict[f][0] != files_b_dict[f][0]:
                total_files_changed += 1
                lines.append("-%s" % files_b_dict[f][0])
                lines.append("+%s" % files_a_dict[f][0])

        sorted_lines = sorted(lines, key=lambda l: l[1:])
        print("\n".join(sorted_lines))

        print(" site A: %d files  site B: %d files" % (len(files_a), len(files_b)))
        print(" %d file changes, %d file additions, %d file deletions)" % (total_files_changed, total_files_added, total_files_deleted))


