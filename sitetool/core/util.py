# SiteTool


import logging
import humanize
import time
from dateutil import tz
import datetime

logger = logging.getLogger(__name__)


class bcolors_color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    ADDED = OKGREEN
    REMOVED = FAIL
    CHANGED = WARNING

    ADDED_SIGN = ADDED + '+' + ENDC
    REMOVED_SIGN = REMOVED + '-' + ENDC
    CHANGED_RIGHT_SIGN = CHANGED + '>' + ENDC
    CHANGED_LEFT_SIGN = CHANGED + '<' + ENDC


class bcolors_nocolor:
    HEADER = ''
    OKBLUE = ''
    OKGREEN = ''
    WARNING = ''
    FAIL = ''
    ENDC = ''
    BOLD = ''
    UNDERLINE = ''

    ADDED = OKGREEN
    REMOVED = FAIL
    CHANGED = WARNING

    ADDED_SIGN = ADDED + '+' + ENDC
    REMOVED_SIGN = REMOVED + '-' + ENDC
    CHANGED_RIGHT_SIGN = CHANGED + '>' + ENDC
    CHANGED_LEFT_SIGN = CHANGED + '<' + ENDC


bcolors = bcolors_color


def utcnow():
    raise NotImplementedError()


def timeago(utcdatetime):

    #datetime = utcdatetime.astimezone().replace(tzinfo=None)
    to_zone = tz.tzlocal()
    localized = utcdatetime.astimezone(to_zone)
    localized_naive = datetime.datetime.fromtimestamp(time.mktime(localized.timetuple()))

    return humanize.naturaltime(localized_naive)


def formatdate(utcdatetime):
    to_zone = tz.tzlocal()
    localized = utcdatetime.astimezone(to_zone)
    localized_naive = datetime.datetime.fromtimestamp(time.mktime(localized.timetuple()))

    return str(localized_naive)

