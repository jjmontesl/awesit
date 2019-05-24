import yaml
import requests
import webbrowser


class Site():
    '''
    '''

    @staticmethod
    def parse_site_env(value):
        (site, env) = value.strip().split(':')
        return (site, env)

