# SiteTool

import os
import requests
import sys
import json
import datetime


class PHPFiles():
    '''
    '''

    url = None
    path = None
    ignore = None

    def file_list(self, remote_path, depth=None):

        final_path = os.path.join(self.path, remote_path)

        url = self.url
        data = {'secret': self.secret,
                'command': 'file_list',
                'path': final_path}

        r = requests.post(url, data)
        fileinfo = json.loads(r.text)

        result = []
        for file in fileinfo:
            #print(file)

            file_path_abs = file[3]
            file_path_rel = "/" + file_path_abs[len(final_path):]

            matches = False
            if self.ignore:
                for ignore in self.ignore:
                    if file_path_rel.startswith(ignore):
                        matches = True
                        break
            if matches:
                continue

            result.append((os.path.dirname(file_path_abs),
                           os.path.basename(file_path_abs),
                           file[2],
                           datetime.datetime.fromtimestamp(file[0]),
                           datetime.datetime.fromtimestamp(file[1])))

        return result

