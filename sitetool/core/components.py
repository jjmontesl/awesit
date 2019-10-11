# SiteTool


import logging
import datetime
from sitetool.core.exceptions import SiteToolException


logger = logging.getLogger(__name__)


class SiteToolComponent():
    '''
    '''

    def __init__(self, ctx):
        self.ctx = ctx

    def initialize(self, ctx):
        raise NotImplementedError("Component %s does not implement initialization properly." % type(self))

    def setting(self, setting, type, value):
        """
        Evaluates a setting value by combining current value with environment,
        site and global settings.
        """
        # Get settings
        result = self.ctx.get('settings').setting(setting) if 'settings' in self.ctx else value
        #logger.info("(E) Setting: %s  Type: %s  My Value: %s  (Base Value: %s): %s", setting, type, my_value, base_value, result)
        return result


class SiteComponent(SiteToolComponent):

    def __init__(self, ctx, site):
        super().__init__(ctx)
        self.site = site  # Actually a SiteEnv

    def initialize(self, ctx, site):
        self.ctx = ctx
        self.site = site

    def setting(self, setting, type, value):
        """
        Evaluates a setting value by combining current value with environment,
        site and global settings.
        """
        # Get settings
        base_value = self.site.setting(setting, type)
        result = SiteToolSettings.combine(base_value, value, type)
        #logger.info("Setting: %s  Type: %s  Value: %s  (Base Value: %s): %s", setting, type, value, base_value, result)
        return result


class SiteToolSettings(SiteToolComponent):

    def __init__(self, ctx, config):
        super().__init__(ctx)
        self.settings = config

    def initialize(self, ctx):
        self.ctx = ctx

    def setting(self, setting, default=None):
        result = self.settings.get(setting, default)
        #logger.debug("Setting: %s Default: %s => %s", setting, default, result)
        return result

    @staticmethod
    def combine(base_value, override_value, type):
        # Combine
        result = None
        if base_value:
            result = base_value

        if override_value:
            if type == 'array-extend':
                result = result if result is not None else []
                result.extend(override_value)
            else:
                raise SiteToolException("Cannot combine settings, unknown combine type: '%s'" % type)

        return result


