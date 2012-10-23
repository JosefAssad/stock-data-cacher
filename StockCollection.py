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

import hashlib
from datetime import date, timedelta
import os
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.exc import IntegrityError
from model import Stock, Day, Datapoint, init_model
import pdb
import urllib2
from urllib2 import HTTPError

class StockCollection(object):

    def __init__(self, settings):
        self.settings = settings
        self.engine = create_engine(self.settings.db_url)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.stocks = []
        meta = MetaData(self.engine)
        meta.reflect()
        if len(meta.tables) == 0: self.create_db()
        session = self.Session()
        for stock in session.query(Stock): self.stocks.append(stock)

    def validate_symbol(self, symbol):
        if "." in symbol:
            # some stocks with . in name cannot be looked up UGLYHACK
            return [symbol, False]
        if "-" in symbol:
            [lhs, rhs] = symbol.split("-")
            cleaned_symbol = lhs + "-P" + rhs
            # UGLYHACK the url doesn't work and y! has no data for
            # this stock even after fixing the symbol
            return [cleaned_symbol, False]
        else:
            return [symbol, True]

    def load_symbols(self, settings):
        for symbols_file in settings.symbols_files:
            input_file = open(symbols_file[u'file'])
            market = symbols_file[u'name']
            lines = iter(input_file)
            lines.next()
            for line in lines:
                [symbol, name] = line.split(u"\t")
                [symbol,  symbol_is_valid] = self.validate_symbol(symbol)
                if symbol_is_valid:
                    if name[:-2] == "": name=None
                    else: name=name[:-2]
                    self.add_stock(unicode(symbol), unicode(name), unicode(market))
                else:
                    # discarding symbol, couldn't validate
                    pass
            input_file.close()

    def update_db(self):
        for stock in self.stocks:
            self.update_stock_in_db(stock)

    def ensure_day_in_db(self, date):
        session = self.Session()
        try:
            day = session.query(Day).filter(Day.date == date).one()
        except:
            day = Day(date)
            session.add(day)
            session.commit()
        return day

    def parse_csv_line(self, line):
        """Takes as input a line of text formatted like
        from Yahoo finance. Example:
        2011-11-14,63.44,63.54,62.93,63.05,6832800,63.05

        Returns a dict with the parsed values.

        """
        def dollah_to_cents(s):
            [lhs, rhs] = s.split(".")
            return (int(lhs)*100)+int(rhs)
        result = {}
        vals = line.split(",")
        result['open_val'] = dollah_to_cents(vals[1])
        result['high'] = dollah_to_cents(vals[2])
        result['low'] = dollah_to_cents(vals[3])
        result['close'] = dollah_to_cents(vals[4])
        result['volume'] = int(vals[5])
        result['adj_close'] = dollah_to_cents(vals[6])
        result['date'] = date(year=int(vals[0][:4]),
                              month=int(vals[0][5:7]),
                              day=int(vals[0][-2:]))
        return result

    def update_stock_in_db(self, stock, start_date=None, end_date=None):
        """Brings the data base for the symbol
        up to date against local cache.

        To maintain integrity, incremental updating is assumed.
        To update incrementally, omit the start_date and end_date
        parameters.

        """
        session = self.Session()
        datapoint_queue = []
        if not start_date:
            if not stock.last_db_update:
                start_date = self.settings.start_date
            else:
                start_date = stock.last_db_update + timedelta(days=1)
        if not end_date: end_date = self.settings.today
        cache_file = open(self.get_cache_file_path(stock.symbol, stock.market))
        for line in cache_file.read().split("\n"):
            if line == "": continue
            values = self.parse_csv_line(line)
            if start_date <= values['date'] <= end_date:
                datapoint_queue.append(values)
        for dp in datapoint_queue:
            if self.settings.assume_days_prepopulated is False:
                day = self.ensure_day_in_db(dp['date'])
            else: day = session.query(Day).filter_by(date=values['date']).one()
            d = Datapoint(stock_id = stock.id,
                          day_id = day.id,
                          open_val = dp["open_val"],
                          high = dp["high"],
                          low = dp["low"],
                          close = dp["close"],
                          volume = dp["volume"],
                          adj_close = dp["adj_close"])
            session.add(d)
            if self.settings.assume_datapoints_unique == False:
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
        stock.last_db_update = end_date
        session.commit()
        cache_file.close()

    def add_stock(self, symbol, name, market):
        stock_registered = False
        stock = Stock(symbol=symbol, name=name, market=market)
        session = self.Session()
        session.add(stock)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        for s in self.stocks:
            if s.symbol == stock.symbol and s.market == stock.market: stock_registered = True
        if not stock_registered: self.stocks.append(stock)
        self.ensure_cache_file_exists(symbol, market)

    def ensure_cache_file_exists(self, symbol, market):
        if not os.path.exists(self.get_cache_file_path(symbol, market)):
            _ = open(self.get_cache_file_path(symbol, market), 'w').close()
        try:
            _ = open(self.get_cache_file_path(symbol, market), mode='r')
        except IOError:
            _ = open(self.get_cache_file_path(symbol, market), mode='a')

    def get_cache_file_path(self, symbol, market):
        return self.settings.cache_dir+"/"\
               + market + u"_" + symbol + u".csv"

    def wipe(self):
        session = self.Session()
        for stock in self.stocks:
            try:
                os.remove(self.get_cache_file_path(stock.symbol, stock.market))
            except OSError:
                # TODO WE SHOULDN'T GET HERE. Log it at least
                pass
            session.delete(stock)
        self.stocks = []
        session.close_all()
        meta = MetaData(self.engine)
        meta.reflect()
        meta.drop_all()

    def create_db(self):
        init_model(self.engine)

    def update_cache(self, start_date=None, end_date=None):
        """updates the cache on all stocks contained

        """
        if not start_date: start_date = self.settings.start_date
        if not end_date: end_date = self.settings.today
        for stock in self.stocks:
            self.load_date_range(stock, start_date, end_date)
            self.dedupe(stock.symbol, stock.market)

    def compose_yahoo_url(self, symbol, startdate, enddate):
        a = unicode(startdate.month - 1)
        b = unicode(startdate.day)
        c = unicode(startdate.year)
        d = unicode(enddate.month - 1)
        e = unicode(enddate.day)
        f = unicode(enddate.year)
        url = u"http://ichart.finance.yahoo.com/table.csv?s=" +\
              symbol + "&a=" + \
              a + "&b=" + b + "&c=" + c + "&d=" + \
              d + "&e=" + e + "&f=" + f + "&g=d&ignore=.csv"
        return url

    def load_date_range(self, stock, start_date=None, end_date=None):
        """ fetches the csv for the date range starting from settings.start_date
        inclusive and ending in the parameter end_date
        appends it to the cache file with no respect for dupes.

        Returns False in case of failure, number of rows appended if success.
        """
        if not start_date:
            if not self.stock.last_cache_update:
                start_date = self.settings.start_date
            else:
                start_date = stock.last_cache_update + timedelta(days=1)
        if not end_date: end_date = self.settings.today
        url = self.compose_yahoo_url(stock.symbol, start_date, end_date)
        num_appended = 0
        cache_file = open(self.get_cache_file_path(stock.symbol, stock.market), 'a')
        try:
            data = urllib2.urlopen(url).read()
        except HTTPError:
            return False
        lines = data.split("\n")[1:-1]
        for line in lines:
            line += "\n"
            cache_file.write(line)
            num_appended += 1
        cache_file.flush()
        cache_file.close()
        stock.last_cache_update = end_date
        return num_appended

    def dedupe(self, symbol, market):
        """removes duplicates
        uses sha1 sums to detect duplicates.
        Returns int with number of dupes found.
        """
        hashes = []
        unique_lines = []
        dupes_found = 0
        cache_file = open(self.get_cache_file_path(symbol, market), 'r')
        for line in cache_file:
            h = hashlib.sha1(line).hexdigest()
            if h not in hashes:
                hashes.append(h)
                unique_lines.append(line)
            else: dupes_found += 1
        cache_file.close()
        cache_file = open(self.get_cache_file_path(symbol, market), 'w')
        for i in unique_lines: cache_file.write(i)
        cache_file.close()
        return dupes_found
