# SiteTool

import logging
import subprocess
import sys
import tempfile

import fabric


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



class SSHMySQLDatabase():
    """
    """

    ssh_host = None
    ssh_user = None
    ssh_port = None

    sudo = False

    db_host = '127.0.0.1'
    db_user = None
    db_password = None
    db_name = None

    def _ssh_get_user(self):
        return self.ssh_user

    def dump(self):
        """
        """
        #remote_backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-remote-backup-')  # FIXME: shall be a remote tmporary file

        backup_path = tempfile.mktemp(prefix='sitetool-tmp-db-backup-')
        logger.info("Archiving database (via SSH remote MySQL client) to %s", backup_path)

        with fabric.Connection(host=self.ssh_host, port=self.ssh_port, user=self._ssh_get_user()) as c:
            output = None
            try:
                if self.sudo:
                    output = c.sudo('mysqldump -h %s -u %s -p%s --add-drop-database %s' % (self.db_host, self.db_user, self.db_password, self.db_name), hide=True)  # hide=not self.st.debug, echo=not self.st.debug)
                else:
                    output = c.run('mysqldump -h %s -u %s -p%s --add-drop-database %s' % (self.db_host, self.db_user, self.db_password, self.db_name), hide=True)
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

    def restore(self, path):
        """
        Restores a backup file.
        """
        raise NotImplementedError()
