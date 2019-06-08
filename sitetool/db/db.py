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
import json

logger = logging.getLogger(__name__)


class SSHShellAdaptor():
    """
    """

    ssh_host = None
    ssh_user = None
    ssh_port = None
    sudo = False

    def get_ssh_user(self):
        return self.ssh_user

    def get_ssh_userhost_string(self):
        ssh_user = self.get_ssh_user()
        if ssh_user:
            return "%s@%s" % (ssh_user, self.ssh_host)
        elif self.ssh_host:
            return "%s" % self.ssh_host
        return ''

    def ssh_context(self):
        if self.ssh_host:
            return fabric.Connection(host=self.ssh_host, port=self.ssh_port, user=self.get_ssh_user())
        else:
            # FIXME: Normalize local / SSH connections for different adaptors, this is doing an unneeded/invalid SSH connection
            return fabric.Connection(host="localhost")

    def ssh_run(self, c, command):
        # FIXME: Put this inside a context manager
        if self.sudo:
            output = c.sudo(command, hide=True)
        else:
            output = c.run(command, hide=True)
        output = output.stdout.strip()
        return output


class DatabaseSerializeCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Dump database rows'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("site", help="site:env - site to serialize")
        parser.add_argument("-j", "--json", action="store_true", default=False, help="serialize to JSON format")

        args = parser.parse_args(args)

        self.site = args.site
        self.json = args.json

    def run(self):
        """
        """

        dt_start = datetime.datetime.utcnow()

        (site_name, site_env) = Site.parse_site_env(self.site)
        site = self.ctx.get('sites').site_env(site_name, site_env)
        db = site.comp('db')

        logger.debug("Database serialization: %s", db.get_name())

        db_serialized = db.serialize()

        if self.json:
            print(json.dumps(db_serialized, indent=4))
            sys.exit(0)

        for (table_name, table) in db_serialized.items():
            if True:
                print("@%s" % table_name)
                cw = csv.writer(sys.stdout)
                cw.writerow(table['columns'] if table['columns'] else [])
                for row in table['rows']:
                    #print(row)
                    cw.writerow(row)
                print()

        #print(db_serialized)


class DatabaseDiffCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Compare data in two databases with same schema'

    def __init__(self, ctx):
        self.ctx = ctx

    def parse_args(self, args):

        parser = argparse.ArgumentParser(description=self.COMMAND_DESCRIPTION)
        parser.add_argument("enva", help="site:env - site and environment A")
        parser.add_argument("envb", help="site:env - target backup site and environment")
        parser.add_argument("-s", "--stat", action="store_true", default=False, help="show only diff stats")

        args = parser.parse_args(args)

        self.site_a = args.enva
        self.site_b = args.envb
        self.stat = args.stat

    def string_diff(self, text, n_text):
        """
        http://stackoverflow.com/a/788780
        Unify operations between two compared strings seqm is a difflib.
        SequenceMatcher instance whose a & b are strings
        """
        seqm = difflib.SequenceMatcher(None, text, n_text)
        output = []
        for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
            if opcode == 'equal':
                output.append(seqm.a[a0:a1])
                #output.append("..")
            elif opcode == 'insert':
                #output.append("<font color=red>^" + seqm.b[b0:b1] + "</font>")
                #output.append(" +" + seqm.b[b0:b1] + " ")
                output.append(bcolors.ADDED + seqm.b[b0:b1] + bcolors.ENDC)
            elif opcode == 'delete':
                #output.append("<font color=blue>^" + seqm.a[a0:a1] + "</font>")
                output.append(bcolors.REMOVED + seqm.a[a0:a1] + bcolors.ENDC)
            elif opcode == 'replace':
                # seqm.a[a0:a1] -> seqm.b[b0:b1]
                #output.append("<font color=green>^" + seqm.b[b0:b1] + "</font>")
                output.append(bcolors.CHANGED + seqm.b[b0:b1] + bcolors.ENDC)
            else:
                logger.warn("Unexpected SequenceMatcher opcode.")
        return ''.join(output)

    def run(self):
        """
        """

        dt_start = datetime.datetime.utcnow()

        logger.debug("DB differences: %s - %s", self.site_a, self.site_b)

        (site_a_name, site_a_env) = Site.parse_site_env(self.site_a)
        (site_b_name, site_b_env) = Site.parse_site_env(self.site_b)

        site_a = self.ctx.get('sites').site_env(site_a_name, site_a_env)
        site_b = self.ctx.get('sites').site_env(site_b_name, site_b_env)

        db_a = site_a.comp('db')
        db_b = site_b.comp('db')

        if not db_a or not db_b:
            logger.error("Both sites need to have a configured database to calculate data differences")
            sys.exit(1)

        logger.debug("Serializing databases")

        # TODO: Allow usage of files if serialized versions are stored
        try:
            db_a_serialized = db_a.serialize()
            db_b_serialized = db_b.serialize()
        except Exception as e:
            logger.error("Could not access databases: %s", e)
            sys.exit(2)

        logger.debug("Calculating data differences")
        tables_a = set(db_a_serialized.keys())
        tables_b = set(db_b_serialized.keys())

        tables_added = tables_a - tables_b
        tables_removed = tables_b - tables_a

        # Differences in rows in common tables
        total_tables_changed = 0
        total_rows_added = 0
        total_rows_deleted = 0
        for table in sorted(list(tables_a & tables_b)):
            rows_a = set([tuple(r) for r in db_a_serialized[table]['rows']])
            rows_b = set([tuple(r) for r in db_b_serialized[table]['rows']])
            rows_added = sorted(list(rows_a - rows_b))
            rows_removed = sorted(list(rows_b - rows_a))

            if rows_added or rows_removed:
                total_tables_changed += 1
                total_rows_added += len(rows_added)
                total_rows_deleted += len(rows_removed)

                print(bcolors.OKBLUE + "%% %s" % (table) + bcolors.ENDC + " (%+d, added: %d, removed: %d)" % (len(rows_added) - len(rows_removed), len(rows_added), len(rows_removed)))
                if not self.stat:

                    lines = []

                    # FIXME: Use primary key from infhormation schema!
                    lines_key = defaultdict(dict)

                    for row in rows_added:
                        lines_key[row[0]]['added'] = row
                        lines.append(bcolors.ADDED + "+" + bcolors.ENDC + " %s" % (",".join(row)))
                    for row in rows_removed:
                        lines_key[row[0]]['removed'] = row
                        lines.append(bcolors.REMOVED + "-" + bcolors.ENDC + " %s" % (",".join(row)))

                    for k, l in lines_key.items():
                        if 'added' not in l or 'removed' not in l: continue
                        matchedline = self.string_diff(",".join(l['added']), ",".join(l['removed']))
                        # FIXME: slow way of avoiding repeated add+remove+change
                        lines = [l for l in lines if not l.startswith(bcolors.ADDED_SIGN + ' ' + k) and not l.startswith(bcolors.REMOVED_SIGN + ' ' + k)]
                        lines.append(bcolors.WARNING + ">" + bcolors.ENDC + " %s" % (matchedline))

                    sorted_lines = sorted(lines, key=lambda l: (l[2:], l[0]))

                    print("\n".join(sorted_lines))
                    print("")

        print(" %d table changes (%+d, %d row insertions, %d row deletions)" % (total_tables_changed, total_rows_added - total_rows_deleted, total_rows_added, total_rows_deleted))
        if tables_added:
            print(" %d table additions: %s" % (len(tables_added), tables_added if tables_added else "-"))
        if tables_removed:
            print(" %d table deletions: %s" % (len(tables_removed), tables_removed if tables_removed else "-"))
        #tables_diff = ItemDiff(name, added/removed/changed, )


