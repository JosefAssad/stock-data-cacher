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

from optparse import OptionParser
from StockCollection import StockCollection
import datetime
import settings

def main():
    parser = OptionParser(version="0.1")
    parser.add_option("-R",
                      "--recreate-db",
                      action="store_true",
                      dest="recreate_db",
                      default=False,
                      help="Anno Zero on the db")
    parser.add_option("-S",
                      "--populate-symbols",
                      action="store_true",
                      dest="populate_symbols",
                      default=False,
                      help="prepopulate the symbols table")
    parser.add_option("-u",
                      "--update",
                      action="store_true",
                      dest="update",
                      default=False,
                      help="update the data for all registered symbols")
    parser.add_option("-D",
                      "--deduplicate",
                      action="store_true",
                      dest="dedupe",
                      default=False,
                      help="ticker symbol for the stock")
    (options, args) = parser.parse_args()
    s = StockCollection(settings)
    if options.recreate_db: s.recreate_db()
    elif options.populate_symbols: s.populate_symbols()
    elif options.update: s.update_data()
    elif options.dedupe: print s.dedupe()
    else: parser.print_usage()


if __name__ == "__main__":
    main()
