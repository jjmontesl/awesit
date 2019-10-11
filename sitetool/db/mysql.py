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
import os
import tarfile

logger = logging.getLogger(__name__)


class MySQLDatabase():
    """
    """

    db_host = None
    db_user = None
    db_password = None
    db_name = None

    db_dump_extra = None

    def dump(self):
        """
        """
        backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-backup-')

        logger.info("Archiving database (local MySQL client) to %s", backup_path)

        #mysqldump -h 127.0.0.1 -u root -p --all-databases
        with open(backup_path, 'w') as outfile:
            subprocess.call(["mysqldump", "-h", self.db_host, '-u', self.db_user, '-p%s' % self.db_password,
                             #'--column-statistics=0',
                             '--skip-lock-tables',
                             '--add-drop-database', self.db_name], stdout=outfile)

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
            self.db_host, self.db_user, self.db_password, self.db_name, path)], stdout=sys.stdout)



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
        local_path = tempfile.mktemp(prefix='sitetool-tmp-db-serialize-')
        remote_path = tempfile.mktemp(prefix='sitetool-tmp-db-serialize-remote-')
        tables = self.list_tables()

        items = {}

        with self.ssh_context() as c:

            self.ssh_run(c, 'mkdir "%s"' % remote_path)

            for table in tables:
                sql = "select * from %s;" % table
                command = 'mysql --batch -h %s -u %s -p%s %s -e "%s" > %s/%s' % (self.db_host, self.db_user, self.db_password, self.db_name, sql, remote_path, table)

                output = None
                try:
                    output, errors = self.ssh_run(c, command)
                except Exception as e:
                    # Assume the directory does not exist, but this is bad error handling
                    logger.warn("Error while serializing MySQL database: %s" % e)
                    output = ''

            self.ssh_run(c, 'tar czf "%s.tgz" -C "%s" .' % (remote_path, remote_path))
            self.ssh_run(c, 'rm -rf "%s"' % (remote_path))

            # Download and uncompress
            c.get("%s.tgz" % remote_path, local_path)
            tar = tarfile.open(local_path, "r:gz")
            for member in tar.getmembers():

                table = member.name
                f = tar.extractfile(member)
                if not f: continue
                print(member.name)
                output = f.read()
                output = str(output, "utf8")
                f.close()

                # Process table file
                output = output.replace("\r", "")

                rows = self._process_table_data(output)
                items[table] = {'name': table,
                                'columns': rows[0] if rows else None,
                                'rows': rows[1:] if rows else [],
                                'key': None,
                                'schema': None}

            self.ssh_run(c, 'rm "%s.tgz"' % (remote_path))
            os.unlink(local_path)

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
        remote_path = tempfile.mktemp(prefix='sitetool-tmp-db-backup-remote-')
        logger.info("Dummping database (via SSH remote MySQL client) to %s", remote_path)

        with self.ssh_context() as c:
            command = 'mysqldump -h %s -u %s -p%s --skip-lock-tables --add-drop-database %s | gzip > "%s.sql.gz"' % (self.db_host, self.db_user, self.db_password, self.db_name, remote_path)
            try:
                output, errors = self.ssh_run(c, command)
            except Exception as e:
                # Assume the directory does not exist, but this is bad error handling
                logger.warn("Error while dumping MySQL database through SSH: %s" % e)
                output = ''

            logger.info("Retrieving database backup.")
            backup_path += ".sql.gz"
            c.get("%s.sql.gz" % remote_path, backup_path)

            self.ssh_run(c, 'rm "%s.sql.gz"' % (remote_path))

        # FIXME: should be a tar_gz (?)
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

