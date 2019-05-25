# SiteTool
import logging
import subprocess
import sys


logger = logging.getLogger(__name__)


class MySQLDatabase():
    """
    """

    def dump(self):
        """
        """
        backup_path = "/tmp/sitetool-db-backup.sql"

        logger.info("Archiving database (local MySQL client) to %s", backup_path)

        #mysqldump -h 127.0.0.1 -u root -p --all-databases
        with open(backup_path, 'w') as outfile:
            subprocess.call(["mysqldump", "-h", self.host, '-u', self.user, '-p%s' % self.password, '--add-drop-database', '--databases', self.db], stdout=outfile)

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

