# SiteTool



import logging
import datetime

from sitetool.files.backup import BackupCommand, BackupListCommand
from sitetool.files.deploy import DeployCommand
from sitetool.browser import BrowserCommand

logger = logging.getLogger(__name__)


class SiteTool():
    '''
    '''

    debug = False

    config = None
    config_path = None

    commands = {'backup': BackupCommand,
                'backup-list': BackupListCommand,

                'deploy': DeployCommand,

                'browser': BrowserCommand}

    def __init__(self):
        #self.ctx = Context()
        #self.ctx.cf = self

        #self.events = EventDispatcher(self)

        #self.object_builder = ObjectBuilder(self)
        #self.executor_pool = ThreadPoolExecutor(8)
        pass

    def initialize(self):
        self.ctx = self.config

        for site_name, site in self.ctx['sites'].items():
            site['name'] = site_name
            for env_name, env in site['envs'].items():
                env['name'] = env_name
                env['site'] = site

    def run(self, command):
        logger.info("Running: %s", command)

        self.backup()


    '''
    def add_from_config(self, config):
        """
        """

        comp_type = config['type']

        try:
            cls = class_from_name(comp_type)
        except ModuleNotFoundError as e:
            logger.critical("Could not create component of type '%s' from config: %s", comp_type, e)
            raise
        except AttributeError as e:
            logger.critical("Could not create component of type '%s' from config: %s", comp_type, e)
            raise

        attribs = {k: self.process_value(v) for (k, v) in config.items()}

        comp = self.object_builder.build(cls, attribs)

        comp_id = config.get('id', None)
        desc = self.ctx.add(comp, comp_id)

        if isinstance(comp, Component) and not comp.id:
            comp.id = desc.id

        return comp

    def process_value(self, value):
        """
        Resolve special values (reference injectors, etc).
        """
        if isinstance(value, dict):
            if 'type' in value:
                return self.add_from_config(value)
            elif 'ref' in value:
                return Inject(value)
            else:
                newdict = {k: self.process_value(v) for k, v in value.items()}
                newobj = self.ctx.add(newdict).object
                return newobj

        elif isinstance(value, list):
            return [self.process_value(i) for i in value]

        elif isinstance(value, str) and value:
            # Interpretate strings starting with @ as references
            if value[0] == '@':
                return Inject(value[1:])

        return value
    '''


if __name__ == "__main__":
    from .bootstrap import Bootstrap
    bootstrap = Bootstrap()
    bootstrap.main()
