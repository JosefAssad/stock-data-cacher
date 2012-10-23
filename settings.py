#!/usr/bin/env python

# Copyright 2012 Josef Assad
#
# This file is part of Stock Data Cacher.
#
# Stock Data Cacher is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Stock Data Cacher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Stock Data Cacher.  If not, see <http://www.gnu.org/licenses/>.

import datetime

db_url=u"postgresql://stocksie:stocksie@localhost/stocksie"
logfile="stocksie.log"

# when do we want our data to start from
start_date = datetime.date(year=2012, month=1, day=1)

# shall loading rows assume the row isn't pre-existing?
# true gives about 20% faster loading, but is potentially unsafe
assume_datapoints_unique=False

# preload days so we don't need to check for their existence?
# If we turn this on, we need to run the day population function before adding data.
# running the day population function is relatively safe; preserves existing day records
assume_days_prepopulated=False

# if we turn this on, symbol population will assume unique lines. Probably slower
# performance. Just leave as true.
guard_against_dupe_symbols=True

# file containing list of stock symbol data
symbols_files=[{u'name':u'NYSE', u'file':u"data/NYSE_full.txt"}]

# for testing purposes. Needs to be set to today() otherwise
today=datetime.date.today()

# following path can be relative or absolute but MUST
cache_dir="cache"
