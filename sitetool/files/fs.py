# SiteTool

import yaml
import requests
import webbrowser


class FSFiles():
    '''
    This driver can access several filesystem types (local, FTP, SFTP, SCP, FTPS, HTTP...).

    It cannot, however, provide entire directory archives directly.
    '''

    def archive(self):
        """
        Archives files and provide a single stream for archived files.
        """
        raise NotImplementedError("VSFiles does not implement an archive operation.")

