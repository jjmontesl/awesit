# SiteTool

import logging
import subprocess
import sys
import tempfile

import fabric
import invoke
import csv
import io

from sitetool.db.db import SSHShellAdaptor

logger = logging.getLogger(__name__)


class SQLiteDatabase(SSHShellAdaptor):
    """
    """
    db_name = None

    def get_name(self):
        """
        Returns a URL-like label for this database.
        """
        return "%s:%s" % (self.get_ssh_userhost_string(), self.db_name.lstrip('/'))

    def list_tables(self):
        logger.debug("Listing SQLite tables from: %s", self.get_name())

        with self.ssh_context() as c:
            sql = "select name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            command = 'sqlite3 -csv "%s" "%s"' % (self.db_path, sql)
            output = None
            try:
                if self.sudo:
                    output = c.sudo(command, hide=True)
                else:
                    output = c.run(command, hide=True)
                output = output.stdout.strip()
            except Exception as e:
                # Assume the directory does not exist, but this is bad error handling
                logger.warn("Error while listing SQLite database tables: %s" % e)
                output = ''

        tables = output.split("\n")

        return tables

    def serialize(self):
        logger.debug("Serializing SQLite data: %s", self.get_name())
        tables = self.list_tables()

        items = {}

        with self.ssh_context() as c:

            for table in tables:
                sql = "select * from '%s';" % table
                command = 'sqlite3 -csv -header "%s" "%s"' % (self.db_path, sql)
                #logger.debug("Dumping SQLite data in CSV format: %s" % command)

                output = None
                try:
                    if self.sudo:
                        output = c.sudo(command, hide=True)
                    else:
                        output = c.run(command, hide=True)
                    output = output.stdout.strip()
                except Exception as e:
                    # Assume the directory does not exist, but this is bad error handling
                    logger.warn("Error while serializing SQLite database: %s" % e)
                    output = ''

                items[table] = self._process_table_data(output)

        return items

    def _process_table_data(self, output):

        items = []

        fileio = io.StringIO(output)
        #reader = csv.DictReader(fileio, delimiter=',', quotechar='"')
        reader = csv.reader(fileio)
        for row in reader:
            items.append(row)

        return items

    def dump(self):
        """
        """
        raise NotImplementedError()
        #remote_backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-remote-backup-')  # FIXME: shall be a remote tmporary file

    def restore(self, path):
        """
        Restores a backup file.
        """
        raise NotImplementedError()


