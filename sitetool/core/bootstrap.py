# SiteTool

import argparse
import functools
import logging
import os
import sys
import yaml

from sitetool.core.sitetool import SiteTool
import warnings
#from Crypto.pct_warnings import RandomPool_DeprecationWarning


logger = logging.getLogger(__name__)


class Bootstrap():
    '''
    '''

    def initialize_logging(self, st):

        # In absence of file config
        default_level = logging.INFO if not st.debug else logging.DEBUG
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)

        if st.debug:
            logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', level=default_level)
            #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        else:
            logging.basicConfig(format='%(message)s', level=default_level)


    def configure_logging(self, st):

        #if 'SITETOOL_LOGGING' not in st.config:
        #    return
        #for key, val in st.config['CF_LOGGING'].items():
        #    logging.getLogger(key).setLevel(logging.getLevelName(val))
        warnings.filterwarnings(action='ignore',module='.*paramiko.*')
        logging.getLogger('paramiko.transport').setLevel(logging.WARN)
        logging.getLogger('invoke').setLevel(logging.WARN)

    def parse_args(self, st):

        usage = 'sitetool [-h] [-d] [-c CONFIG] command [command options]\n\n'
        usage = usage + "  Commands:\n"
        for command_name, command in st.commands.items():
            usage = usage + "    %s\n" % (command_name)

        parser = argparse.ArgumentParser(usage=usage, add_help=False)  # description='', usage = ''
        parser.add_argument("-d", "--debug", action="store_true", default=False, help="debug logging")
        parser.add_argument("-c", "--config", default="~/.sitetool.conf", help="config file")
        parser.add_argument("command", nargs='?', default=None, help="subcommand to run")
        #parser.add_argument("rest", nargs='*')

        args, unknown = parser.parse_known_args()  # sys.argv[1:]

        st.debug = args.debug
        st.config_path = args.config

        if args.command not in st.commands:
            if args.command:
                print('Unrecognized command: %r' % args.command)
            parser.print_help()
            sys.exit(1)

        command_class = st.commands[args.command]
        st.command = command_class(st)

        st.command.parse_args(unknown)  #args.rest)

    def read_config(self, st):
        final_path = os.path.expanduser(st.config_path)

        logger.debug("Reading Sitetool config from: %s", final_path)
        #logger.warn("TODO: Using YAML unsafe loader (use FullLoader instead).")
        try:
            with open(final_path, 'r') as stream:
                try:
                    st.config = yaml.load(stream, Loader=yaml.UnsafeLoader)
                except yaml.YAMLError as e:
                    logger.error("Could not read config file '%s': %s", st.config_path, e)
                    sys.exit(2)
        except Exception as e:
            logger.error("Could not read configuration file: %s (%s)", st.config_path, e)
            sys.exit(1)

        #logger.debug("SiteTool configuration: %s", st.config)

    def _config_include(self, config, current_file, include_path):

        config_path = os.path.join(os.path.dirname(current_file or "."), include_path)
        config_path = os.path.abspath(config_path)

        if not current_file:
            logger.info("Loading config file: %s", config_path)
        else:
            logger.debug("Including config file: %s", config_path)

        config_include = functools.partial(self._config_include, config, config_path)

        with open(config_path) as f:
            pass
            '''
            code = compile(f.read(), config_path, 'exec')
            exec(code, {'SITETOOL_INCLUDE': config_include}, config)

            logger.debug("Initializing : %s", comp.object)
            try:
                #comp.object.initialize()
                #comp.object.state = INITIALIZED
            except Exception as e:
                logger.exception("Error initializing component '%s': %s" % (comp, e))
            '''

    def main(self, app_name="SiteTool", app_version="0.0.1"):

        st = SiteTool()

        self.parse_args(st)
        self.initialize_logging(st)

        logger.debug("Starting %s %s" % (app_name, app_version))

        self.read_config(st)
        self.configure_logging(st)

        st.initialize()

        # Run command
        try:
            st.command.run()
        except KeyboardInterrupt as e:
            logger.info("Process interrupted by keyboard interrupt.")

        logger.debug("Service finishing.")


def main():
    """
    Application entry point.
    """
    bootstrap = Bootstrap()
    bootstrap.main()  # sys.argv[1:]

