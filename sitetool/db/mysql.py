# SiteTool

import logging
import subprocess
import sys
import tempfile

import fabric
from sitetool.db.db import SSHShellAdaptor
import csv
import io
from sitetool.core.exceptions import SiteToolException

logger = logging.getLogger(__name__)


class MySQLDatabase():
    """
    """

    #db_host = None
    #db_pass = None
    #db_user = None
    #db_port = None

    db_dump_extra = None

    def dump(self):
        """
        """
        backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-backup-')

        logger.info("Archiving database (local MySQL client) to %s", backup_path)

        #mysqldump -h 127.0.0.1 -u root -p --all-databases
        with open(backup_path, 'w') as outfile:
            subprocess.call(["mysqldump", "-h", self.host, '-u', self.user, '-p%s' % self.password,
                             #'--column-statistics=0',
                             '--skip-lock-tables',
                             '--add-drop-database', self.db], stdout=outfile)

        # FIXME: should be a tar_gz
        subprocess.call(["gzip", backup_path])
        backup_path += ".gz"

        backup_md5sum = None

        return (backup_path, backup_md5sum)

    def restore(self, path):
        """
        Restores a backup file.
        """
        logger.info("Restoring database (local MySQL client) from %s to %s@%s:%s", path, self.user, self.host, self.db)

        logger.info("Uncompressing backed up database.")
        subprocess.call(["mv", path, path + ".gz"])
        subprocess.call(["gunzip", path + ".gz"])

        logger.info("Loading database.")
        subprocess.call(["/bin/bash", "-c", 'mysql -h "%s" -u "%s" -p%s %s < %s' % (
            self.host, self.user, self.password, self.db, path)], stdout=sys.stdout)



class SSHMySQLDatabase(SSHShellAdaptor):
    """
    """

    db_host = '127.0.0.1'
    db_user = None
    db_password = None
    db_name = None

    def get_name(self):
        """
        Returns a URL-like label for this database.
        """
        return "%s:%s" % (self.get_ssh_userhost_string(), self.db_name)

    def list_tables(self):
        logger.debug("Listing SQLite tables from: %s", self.get_name())

        with self.ssh_context() as c:
            #sql = "select * from schema.table;"
            sql = "show tables;"
            command = 'mysql --batch -h %s -u %s -p%s %s -e "%s"' % (self.db_host, self.db_user, self.db_password, self.db_name, sql)
            output = None
            try:
                if self.sudo:
                    output = c.sudo(command, hide=True)
                else:
                    output = c.run(command, hide=True)
                output = output.stdout.strip()
            except Exception as e:
                # Assume the directory does not exist, but this is bad error handling
                raise SiteToolException("Error while listing MySQL database tables: %s" % e)

        tables = output.split("\n")

        if len(tables) > 0:
            tables = tables[1:]

        return tables

    def serialize(self):
        logger.debug("Serializing MySQL data: %s", self.get_name())
        tables = self.list_tables()

        items = {}

        with self.ssh_context() as c:

            for table in tables:
                sql = "select * from %s;" % table
                command = 'mysql --batch -h %s -u %s -p%s %s -e "%s"' % (self.db_host, self.db_user, self.db_password, self.db_name, sql)

                output = None
                try:
                    if self.sudo:
                        output = c.sudo(command, hide=True)
                    else:
                        output = c.run(command, hide=True)
                    output = output.stdout  #.strip()
                except Exception as e:
                    # Assume the directory does not exist, but this is bad error handling
                    logger.warn("Error while serializing MySQL database: %s" % e)
                    output = ''

                output = output.replace("\r", "")

                rows = self._process_table_data(output)
                items[table] = {'name': table,
                                'columns': rows[0] if rows else None,
                                'rows': rows[1:] if rows else [],
                                'key': None,
                                'schema': None}

        return items

    def _process_table_data(self, output):

        items = []

        fileio = io.StringIO(output)
        #reader = csv.DictReader(fileio, delimiter=',', quotechar='"')
        reader = csv.reader(fileio, delimiter='\t', quotechar=None)
        for row in reader:
            items.append(row)

        return items

    def dump(self):
        """
        """
        #remote_backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-remote-backup-')  # FIXME: shall be a remote tmporary file

        backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-backup-')
        logger.info("Archiving database (via SSH remote MySQL client) to %s", backup_path)

        with fabric.Connection(host=self.ssh_host, port=self.ssh_port, user=self.get_ssh_user()) as c:
            output = None
            try:
                if self.sudo:
                    output = c.sudo('mysqldump -h %s -u %s -p%s --skip-lock-tables --add-drop-database %s' % (self.db_host, self.db_user, self.db_password, self.db_name), hide=True)  # hide=not self.st.debug, echo=not self.st.debug)
                else:
                    output = c.run('mysqldump -h %s -u %s -p%s --skip-lock-tables --add-drop-database %s' % (self.db_host, self.db_user, self.db_password, self.db_name), hide=True)
                output = output.stdout.strip()
            except Exception as e:
                # Assume the directory does not exist, but this is bad error handling
                logger.warn("Error while dumping MySQL database through SSH: %s" % e)
                output = ''



        with open(backup_path, 'w') as outfile:
            outfile.write(output)

        # FIXME: should be a tar_gz (?)
        subprocess.call(["gzip", backup_path])
        backup_path += ".gz"

        backup_md5sum = None

        return (backup_path, backup_md5sum)

    def restore(self, local_path):
        """
        Restores a backup file.
        """
        logger.info("Restoring database from %s to %s", local_path, self.get_name())

        remote_path = tempfile.mktemp(prefix='sitetool-tmp-')

        with self.ssh_context() as c:
            result = c.put(local_path, remote_path)
            logger.info("Uncompressing database.")
            self.ssh_run(c, 'mv "%s" "%s.sql.gz"' % (remote_path, remote_path))
            self.ssh_run(c, 'gunzip "%s.sql.gz"' % (remote_path))
            logger.info("Loading database.")
            self.ssh_run(c, 'mysql -h "%s" -u "%s" -p%s %s < "%s.sql"' % (self.db_host, self.db_user, self.db_password, self.db_name, remote_path))
            self.ssh_run(c, 'rm "%s.sql"' % (remote_path))

