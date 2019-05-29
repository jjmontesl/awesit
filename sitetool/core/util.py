# SiteTool


import logging
import humanize
import time
from dateutil import tz
import datetime

logger = logging.getLogger(__name__)


def timeago(utcdatetime):

    #datetime = utcdatetime.astimezone().replace(tzinfo=None)
    to_zone = tz.tzlocal()
    localized = utcdatetime.astimezone(to_zone)
    localized_naive = datetime.datetime.fromtimestamp(time.mktime(localized.timetuple()))

    return humanize.naturaltime(localized_naive)
