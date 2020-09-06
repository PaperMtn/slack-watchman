import calendar
import time

# Epoch time for 24 hours
DAY_TIMEFRAME = 86400
# Epoch time for 30 days
MONTH_TIMEFRAME = 2592000
# Epoch time for 7 days
WEEK_TIMEFRAME = 604800
# Epoch time for a very long time
ALL_TIME = calendar.timegm(time.gmtime()) + 1576800000