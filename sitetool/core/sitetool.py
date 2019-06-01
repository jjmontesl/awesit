# SiteTool



import logging
import datetime

from sitetool.backup.backup import BackupCommand, BackupListCommand, BackupDeleteCommand,\
    BackupManager
from sitetool.backup.deploy import BackupDeployCommand
from sitetool.browser import BrowserCommand
from sitetool.sites import SiteManager, SitesListCommand
from sitetool.files.files import FilesListCommand, FilesDiffCommand
from sitetool.db.db import DatabaseSerializeCommand, DatabaseDiffCommand
from sitetool.joomla.joomla import JoomlaInfoCommand
from sitetool.core.components import SiteToolSettings
from sitetool.data.data import DataFilesExportCommand

logger = logging.getLogger(__name__)


class SiteTool():
    '''
    '''

    debug = False

    config = None
    config_path = None

    commands = {'sites': SitesListCommand,

                'backup': BackupCommand,
                'backup-list': BackupListCommand,
                'backup-delete': BackupDeleteCommand,
                #'backup-deploy': BackupDeployCommand,
                'deploy': BackupDeployCommand,

                'files': FilesListCommand,
                'files-diff': FilesDiffCommand,
                #'files-sync': FilesSyncCommand,

                'db-serialize': DatabaseSerializeCommand,
                'db-diff': DatabaseDiffCommand,
                #'db-sync': DatabaseSyncCommand,

                'datafiles-export': DataFilesExportCommand,
                #'data-diff': DataDiffCommand, (?)
                #'data-sync': DataSyncCommand, (import?)

                #'diff': CommonDiffCommand,
                #'sync': CommonSyncCommand,

                'joomla-info': JoomlaInfoCommand,  # ? (w/ extensions, status, etc...)
                #'joomla-upgrade': JoomlaExtensionsUpgradeCommand,
                #'joomla-checks-': (? install folder, etc?)
                #'joomla-ext-list': JoomlaExtensionsListCommand,
                #'joomla-ext-upgrade': JoomlaExtensionsUpgradeCommand, (in upgrade ?)
                #'joomla-ext-install': JoomlaExtensionsInstallCommand,
                #'joomla-data-export': JoomlaExportCommand, ? (or generic export/import providers, writing objects to disk?)
                #'joomla-data-import': JoomlaImportCommand, ?

                'browser': BrowserCommand}

    def __init__(self, ctx):

        self.ctx = ctx

        #self.events = EventDispatcher(self)
        #self.object_builder = ObjectBuilder(self)
        #self.executor_pool = ThreadPoolExecutor(8)

    def initialize(self):

        #self.ctx = self.config

        self.ctx['_sitetool'] = self

        self.ctx['settings'] = SiteToolSettings(self.ctx, self.ctx.get('settings', {}))
        self.ctx['sites'] = SiteManager(self.ctx, self.ctx.get('sites', {}))
        self.ctx['backups'] = BackupManager(self.ctx)

        # Initialize
        for key, c in self.ctx.items():
            if key.startswith("_"):
                continue

            try:
                c.initialize(self.ctx)
            except Exception as e:
                logger.error("Error initializing component: %s", c)
                raise


if __name__ == "__main__":
    from .bootstrap import Bootstrap
    bootstrap = Bootstrap()
    bootstrap.main()
