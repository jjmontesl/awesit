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
from sitetool.core.util import timeago, bcolors
import difflib

import pathspec
from sitetool.core import util
import subprocess

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


class SiteFileList(namedtuple('SiteFileList', 'files errors excluded_count')):
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

    def filenames_filtered(self, filenames):
        # Do not use: added for files-diff, but they should work with SiteFiles always
        excluded = self.files_excluded(filenames)
        excluded_set = set(excluded)
        result = [f for f in filenames if f not in excluded_set]
        return result, len(excluded_set)

    def files_filtered(self, sitefiles):
        excluded = self.files_excluded([f.relpath for f in sitefiles])
        excluded_set = set(excluded)
        result = [f for f in sitefiles if f.relpath not in excluded_set]
        return result, len(excluded_set)


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
        parser.add_argument("-a", "--all", action="store_true", default=False, help="list all files")
        parser.add_argument("-e", "--excluded", action="store_true", default=False, help="list excluded files")
        #parser.add_argument("-f", "--file", default=None, help="show file contents")

        args = parser.parse_args(args)

        self.site = args.site
        self.by_size = args.by_size
        self.by_time = args.by_time
        self.reverse = args.reverse
        self.all = args.all
        self.excluded = args.excluded

        if (self.all and self.excluded):
            logger.error("Cannot list both --all and --excluded files (the two options cannot be used together).")
            sys.exit(1)

    def run(self):
        """
        """

        dt_start = datetime.datetime.utcnow()

        logger.debug("Directory listing: %s", self.site)

        (site_name, site_env) = Site.parse_site_env(self.site)
        site = self.ctx.get('sites').site_env(site_name, site_env)

        # files_comp = self.resolve_files_from_selector_backup_dir(self.site)

        (files, errors, excluded_count) = site.comp('files').file_list('', all=self.all)
        if self.excluded:
            (files_all, errors_all, excluded_count) = site.comp('files').file_list('', all=True)
            files_set = set([f.relpath for f in files])
            files = [f for f in files_all if f.relpath not in files_set]

        files.sort(key=lambda f: f.relpath)

        if self.by_size:
            files.sort(key=lambda x: x.size)
        if self.by_time:
            files.sort(key=lambda x: x.mtime)
        if self.reverse:
            files.reverse()

        for error in errors:
            print("ERROR: %s" % error)

        # Print files
        total_size = 0
        for f in files:
            total_size += f.size
            print("%-20s %10s %s" % (
                util.formatdate(f.mtime),
                f.size,
                f.relpath))

        output = " %d files, %.1f MB" % (len(files), total_size / (1024 * 1024))
        output += "" if not excluded_count else (" (%d excluded)" % excluded_count)
        output += "" if not errors else (" (+%d errors)" % len(errors))
        print(output)


class FilesDiffCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Show differences between two sites file trees'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("enva", help="site:env - site and environment A")
        parser.add_argument("envb", help="site:env - site and environment B")
        parser.add_argument("-t", "--ignore-time", action="store_true", default=False, help="ignore modification times")

        # TODO: Should be a different command?
        parser.add_argument("-f", "--file", default=None, help="diff file between environments")

        args = parser.parse_args(args)

        self.site_a = args.enva
        self.site_b = args.envb
        self.ignore_time = args.ignore_time
        self.file = args.file

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

        if self.file:
            return self.run_file_diff()

        # FIXME: This way of comparing (text-based) is incorrect regarding
        # directory differences

        logger.debug("Directory differences: %s > %s", self.site_a, self.site_b)

        (site_a_name, site_a_env) = Site.parse_site_env(self.site_a)
        (site_b_name, site_b_env) = Site.parse_site_env(self.site_b)

        backup_date = datetime.datetime.now()

        site_a = self.ctx.get('sites').site_env(site_a_name, site_a_env)
        site_b = self.ctx.get('sites').site_env(site_b_name, site_b_env)

        files_a, errors_a, excluded_count_a = site_a.comp('files').file_list('')
        files_b, errors_b, excluded_count_b = site_b.comp('files').file_list('')

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
        files_added, files_added_excluded_count = site_b.comp('files').filenames_filtered(files_added)
        files_removed = sorted(list(files_b_set - files_a_set))
        files_removed, files_removed_excluded_count = site_b.comp('files').filenames_filtered(files_removed)

        lines = []
        size = 0
        for f in files_added:
            total_files_added += 1
            lines.append(bcolors.ADDED_SIGN + bcolors.ADDED + "%s" % (files_a_dict[f][0], ) + bcolors.ENDC)
            size += files_a_dict[f][1].size
        for f in files_removed:
            total_files_deleted += 1
            lines.append(bcolors.REMOVED_SIGN + bcolors.REMOVED + "%s" % (files_b_dict[f][0], ) + bcolors.ENDC)

        files_changed = list(files_a_set & files_b_set)
        files_changed, files_changed_excluded_count = site_b.comp('files').filenames_filtered(files_changed)
        for f in files_changed:
            if ((not self.ignore_time and files_a_dict[f][1].mtime != files_b_dict[f][1].mtime) or
                files_a_dict[f][1].size != files_b_dict[f][1].size):
                size += files_a_dict[f][1].size
                total_files_changed += 1
                #lines.append("-%s" % files_b_dict[f][0])
                #lines.append("+%s" % files_a_dict[f][0])
                direction = bcolors.CHANGED_RIGHT_SIGN if files_a_dict[f][1].mtime >= files_b_dict[f][1].mtime else bcolors.CHANGED_LEFT_SIGN
                lines.append(("%s" % direction) + bcolors.CHANGED + ("%s" % (files_a_dict[f][0])) + bcolors.ENDC)

        sorted_lines = sorted(lines, key=lambda l: l[1:])

        if sorted_lines:
            print("\n".join(sorted_lines))

        print(" source: %d files  target: %d files" % (len(files_a), len(files_b)))
        print(" %d file changes, %d file additions, %d file deletions (%.1fM data)" % (total_files_changed, total_files_added, total_files_deleted, size / (1024*1024)))

    def run_file_diff(self):


        site_a = self.ctx.get('sites').get_site(self.site_a)
        site_b = self.ctx.get('sites').get_site(self.site_b)

        relpath_a = self.file
        relpath_b = self.file

        logger.debug("Calculating differences for: %s:%s -> %s:%s", self.site_a, relpath_a, self.site_b, relpath_b)

        # Get files
        file_a = site_a.comp('files').file_get(relpath_a)
        file_b = site_b.comp('files').file_get(relpath_b)

        # Differences
        subprocess.call(["diff", file_a, file_b])

        os.unlink(file_a)
        os.unlink(file_b)

