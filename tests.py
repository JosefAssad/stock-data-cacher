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

import pdb
import unittest
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import *
import os
import datetime
import hashlib
from nose.tools import with_setup

from StockCollection import StockCollection
from model import Datapoint, Stock, Day
import settings

dp_A_20120323=[u'NYSE', u"A", u"2012-03-23,43.57,44.30,43.15,44.30,3369400,44.20"]
dp_A_20120326=[u'NYSE', u"A", u"2012-03-26,44.87,45.12,44.63,45.05,3467100,44.95"]
dp_A_20120327=[u'NYSE', u"A", u"2012-03-27,45.05,46.28,44.99,45.67,3804100,45.57"]
dp_A_20120328=[u'NYSE', u"A", u"2012-03-28,45.42,45.47,44.09,44.59,3089300,44.49"]
dp_AA_20120323=[u'NYSE', u"AA", u"2012-03-23,10.01,10.26,9.96,10.11,20016500,10.08"]
dp_AA_20120326=[u'NYSE', u"AA", u"2012-03-26,10.25,10.30,10.12,10.22,13772200,10.19"]
dp_AA_20120327=[u'NYSE', u"AA", u"2012-03-27,10.25,10.31,10.06,10.06,19193300,10.03"]
dp_AA_20120328=[u'NYSE', u"AA", u"2012-03-28,10.06,10.06,9.79,9.83,36435200,9.80"]
dp_AAN_20120323=[u'NYSE', u"AAN", u"2012-03-23,25.73,25.83,25.12,25.65,406500,25.65"]
dp_AAN_20120326=[u'NYSE', u"AAN", u"2012-03-26,25.92,26.33,25.90,26.17,537400,26.17"]
dp_AAN_20120327=[u'NYSE', u"AAN", u"2012-03-27,26.12,26.50,26.05,26.06,609900,26.06"]


class testValidation(unittest.TestCase):

    def setUp(self):
        self.settings = settings
        self.stock_collection = StockCollection(self.settings)

    def tearDown(self):
        pass

    def testSymbolValidation(self):
        """Testing validation of stock symbols

        """
        result = self.stock_collection.validate_symbol(u"ABC")
        assert result[1] == True and result[0] == u"ABC",\
               'expected symbol ABC to generate True, instead it generated False'

        result = self.stock_collection.validate_symbol(u"AB.C")
        assert result[1] == False and result[0] == u"AB.C",\
               'expected symbol AB.C to generate False, instead it generated True'

        result = self.stock_collection.validate_symbol(u"AB-C")
        assert result[1] == False and result[0] == u"AB-PC",\
               'expected symbol ABC to generate True and AB-PC, instead it generated [%s, %s]' %\
               (result[0], result[1])


class testSymbolLoading(object):

    def setUp(self):
        self.settings = settings
        self.engine = create_engine(settings.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.stock_collection = StockCollection(self.settings)
        self.stock_collection.wipe()
        self.stock_collection.create_db()

    def tearDown(self):
        cache_file_paths = []
        for stock in self.stock_collection.stocks:
            cache_file_paths.append(self.stock_collection.get_cache_file_path(stock.symbol, stock.market))
        meta = MetaData(bind=self.stock_collection.engine)
        meta.reflect()
        self.stock_collection.wipe()
        for cache_file_path in cache_file_paths:
            assert not os.path.exists(cache_file_path),\
                   'cache file %s was not removed' % cache_file_path
        engine = create_engine(self.settings.db_url)
        meta2 = MetaData(bind=engine)
        meta2.reflect()
        assert len(meta2.tables) == 0, 'tables were not deleted. %s remain.' % len(meta.tables)

    def test_gen(self):
        """testing stock entity loading

        """
        data = []

        def create_test_symbols_file(market_name, full_file, rows):
            outfile_name = 'data/' + market_name + '_test.txt'
            outfile = open(outfile_name, 'w')
            infile = open(full_file, 'r')
            lines = iter(infile)
            for foo in xrange(1, rows+2):
                line = lines.next()
                outfile.write(line)
            outfile.close()
            infile.close()

        tempdata = {u'name':u'NYSE', u'file_full':u'data/NYSE_full.txt', u'file':u"data/NYSE_test.txt", u'stocks':[]}
        tempdata['stocks'].append({u'market':u'NYSE', u'symbol':u'A', u'name':u'Agilent Technologies'})
        tempdata['stocks'].append({u'market':u'NYSE', u'symbol':u'AA', u'name':u'Alcoa Inc.'})
        tempdata['stocks'].append({u'market':u'NYSE', u'symbol':u'AAN', u'name':u'Aaron\'s Inc.'})
        data.append(tempdata)
        tempdata = {'name':u'NASDAQ', u'file_full':u'data/NASDAQ_full.txt', u'file':u"data/NASDAQ_test.txt", u'stocks':[]}
        tempdata['stocks'].append({u'market': u'NASDAQ', u'symbol':u'AAC', u'name':u'Australia Acquisition'})
        tempdata['stocks'].append({u'market': u'NASDAQ', u'symbol':u'AACC', u'name':u'Asset Acceptance Capital'})
        tempdata['stocks'].append({u'market': u'NASDAQ', u'symbol':u'AACOU', u'name':u'Australia Acquisition Corp.'})
        data.append(tempdata)

        max_markets = len(data)
        max_stocks = 3

        for num_markets in xrange(1, max_markets+1):
            markets = data[:num_markets]
            market_files = []
            for market in markets:
                market_files.append({u'name':market[u'name'], u'file':market[u'file']})
            for num_stocks in xrange(1, max_stocks+1):
                for market in markets:
                    create_test_symbols_file(market[u'name'], market[u'file_full'], num_stocks)
                expected_symbols = []
                for d in data[:num_markets]:
                    for s in d['stocks'][:num_stocks]:
                        expected_symbols.append(s)
                yield self.check_symbol_loading_works, market_files, expected_symbols

    @with_setup(setUp, tearDown)
    def check_symbol_loading_works(self, markets_list, expected_symbols):
        session = self.Session()
        stocks_raw = []
        self.settings.symbols_files = markets_list
        self.stock_collection.load_symbols(self.settings)
        for es in expected_symbols:
            stock = self.get_stock_from_db(es['market'], es['symbol'], es['name'])
            assert stock, 'stock \'%s\' not found in db' % es['name']
            assert os.path.exists(self.stock_collection.\
                                  get_cache_file_path(es['symbol'], es['market'])),\
                                  'cache file not found for stock %s' % es['name']
        num_stocks = len(session.query(Stock).all())
        expected_num_stocks = len(expected_symbols)
        assert num_stocks == expected_num_stocks,\
               'expected %s stock in db, found %s' % (expected_num_stocks, num_stocks)

    def testLoad1Symbol1Market(self):
        """loading of 1 symbol, 1 market file

        """
        session = self.Session()
        stocks_raw = []
        self.settings.symbols_files = [{u'name':u'NYSE', u'file':u"data/NYSE_test1.txt"}]
        stocks_raw.append({u'market':u'NYSE', u'symbol':u'A', u'name':u'Agilent Technologies'})
        self.stock_collection.load_symbols(self.settings)
        for stock_raw in stocks_raw:
            stock = self.get_stock_from_db(stock_raw['market'],\
                                           stock_raw['symbol'], stock_raw['name'])
            assert stock, 'stock \'%s\' not found in db' % stock_raw['name']
            assert os.path.exists(self.stock_collection.\
                                  get_cache_file_path(stock_raw['symbol'], stock_raw['market'])),\
                                  'cache file not found for stock %s' % stock_raw['name']
        num_stocks = len(session.query(Stock).all())
        expected_num_stocks = len(stocks_raw)
        assert num_stocks == expected_num_stocks,\
               'expected %s stock in db, found %s' % (expected_num_stocks, num_stocks)


    def get_stock_from_db(self, market, symbol, name=""):
        session = self.Session()
        try:
            if not name:
                stock = session.query(Stock).\
                        filter(Stock.market == market).\
                        filter(Stock.symbol == symbol).one()
                return stock
            else:
                stock = session.query(Stock).\
                        filter(Stock.market == market).\
                        filter(Stock.symbol == symbol).\
                        filter(Stock.name == name).one()
                return stock
        except NoResultFound:
            return False
        except:
            return False

    def testLoad2Symbol1Market(self):
        """loading of 2 symbols, 1 market file

        """
        session = self.Session()
        stocks_raw = []
        self.settings.symbols_files = [{u'name':u'NYSE', u'file':u"data/NYSE_test2.txt"}]
        stocks_raw.append({u'market':u'NYSE', u'symbol':u'A', u'name':u'Agilent Technologies'})
        stocks_raw.append({u'market':u'NYSE', u'symbol':u'AA', u'name':u'Alcoa Inc.'})
        self.stock_collection.load_symbols(self.settings)
        for stock_raw in stocks_raw:
            stock = self.get_stock_from_db(stock_raw['market'], stock_raw['symbol'], stock_raw['name'])
            assert stock, 'stock \'%s\' not found in db' % stock_raw['name']
            assert os.path.exists(self.stock_collection.\
                                  get_cache_file_path(stock_raw['symbol'], stock_raw['market'])),\
                                  'cache file not found for stock %s' % stock_raw['name']
        num_stocks = len(session.query(Stock).all())
        expected_num_stocks = len(stocks_raw)
        assert num_stocks == expected_num_stocks, 'expected %s stock in db, found %s' % (expected_num_stocks, num_stocks)

    def testLoad1Symbol2Market(self):
        """loading of 2 market files 1 symbol each

        """
        session = self.Session()
        stocks_raw = []
        self.settings.symbols_files = [{u'name':u'NYSE', u'file':u"data/NYSE_test1.txt"},
                                       {u'name':u'NASDAQ', u'file':u"data/NASDAQ_test1.txt"}]
        stocks_raw.append({u'market':u'NYSE', u'symbol':u'A', u'name':u'Agilent Technologies'})
        stocks_raw.append({u'market':u'NASDAQ', u'symbol':u'AAC', u'name':u'Australia Acquisition'})
        self.stock_collection.load_symbols(self.settings)
        for stock_raw in stocks_raw:
            stock = self.get_stock_from_db(stock_raw['market'], stock_raw['symbol'], stock_raw['name'])
            assert stock, 'stock \'%s\' not found in db' % stock_raw['name']
            assert os.path.exists(self.stock_collection.\
                                  get_cache_file_path(stock_raw['symbol'], stock_raw['market'])),\
                                  'cache file not found for stock %s' % stock_raw['name']
        num_stocks = len(session.query(Stock).all())
        expected_num_stocks = len(stocks_raw)
        assert num_stocks == expected_num_stocks,\
               'expected %s stock in db, found %s' % (expected_num_stocks, num_stocks)

    def testLoad2Symbol2Market(self):
        """loading of 2 market files 2 symbols each

        """
        session = self.Session()
        stocks_raw = []
        self.settings.symbols_files = [{u'name':u'NYSE', u'file':u"data/NYSE_test2.txt"},
                                       {u'name':u'NASDAQ', u'file':u"data/NASDAQ_test2.txt"}]
        stocks_raw.append({u'market':u'NYSE', u'symbol':u'A', u'name':u'Agilent Technologies'})
        stocks_raw.append({u'market':u'NASDAQ', u'symbol':u'AAC', u'name':u'Australia Acquisition'})
        stocks_raw.append({u'market':u'NYSE', u'symbol':u'AA', u'name':u'Alcoa Inc.'})
        stocks_raw.append({u'market':u'NASDAQ', u'symbol':u'AACC', u'name':u'Asset Acceptance Capital'})
        self.stock_collection.load_symbols(self.settings)
        for stock_raw in stocks_raw:
            stock = self.get_stock_from_db(stock_raw['market'], stock_raw['symbol'], stock_raw['name'])
            assert stock, 'stock \'%s\' not found in db' % stock_raw['name']
            assert os.path.exists(self.stock_collection.\
                                  get_cache_file_path(stock_raw['symbol'], stock_raw['market'])),\
                                  'cache file not found for stock %s' % stock_raw['name']
        num_stocks = len(session.query(Stock).all())
        expected_num_stocks = len(stocks_raw)
        assert num_stocks == expected_num_stocks,\
               'expected %s stock in db, found %s' % (expected_num_stocks, num_stocks)


class testCache(unittest.TestCase):

    def setUp(self):
        self.settings = settings
        self.engine = create_engine(settings.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.stock_collection = StockCollection(self.settings)
        self.stock_collection.wipe()
        self.stock_collection.create_db()

    def tearDown(self):
        cache_file_paths = []
        for stock in self.stock_collection.stocks:
            cache_file_paths.append(self.stock_collection.get_cache_file_path(stock.symbol, stock.market))
        meta = MetaData(bind=self.stock_collection.engine)
        meta.reflect()
        self.stock_collection.wipe()
        for cache_file_path in cache_file_paths:
            assert not os.path.exists(cache_file_path),\
                   'cache file %s was not removed' % cache_file_path
        engine = create_engine(self.settings.db_url)
        meta2 = MetaData(bind=engine)
        meta2.reflect()
        assert len(meta2.tables) == 0, 'tables were not deleted. %s remain.' % len(meta.tables)

    def testUseCase1(self):
        """Testing use case 1
        This use case consists of following steps:
        1. Initialise stock collection
        2. Add 1 stock to it.
        3. Update the cache
        4. Update the db
        5. Wait 1 day then update cache and db again
        6. Add 1 stock
        7. Update cache and db
        8. Wait 1 day, then update cache and db
        """
        session = self.Session()
        # 1. Initialise stock collection was done in setUp()
        # 2. Add 1 stock to it.
        self.settings.symbols_files = [{u'name':u'NYSE', u'file':u"data/NYSE_test1.txt"}]
        self.stock_collection.load_symbols(self.settings)
        assert len(session.query(Stock).\
                   filter(Stock.symbol == u"A").\
                   filter(Stock.name == u"Agilent Technologies").all()) == 1, \
               'error adding stock to db'
        stock = session.query(Stock).\
                filter(Stock.symbol == u"A").\
                filter(Stock.name == u"Agilent Technologies").one()
        assert os.path.exists(self.stock_collection.\
                              get_cache_file_path(stock.symbol, stock.market)), 'foo'
        # 3. Update the cache
        self.stock_collection.settings.start_date = datetime.date(year=2012, month=3, day=23)
        self.stock_collection.settings.today = datetime.date(year=2012, month=3, day=26)
        self.stock_collection.update_cache()
        stock_cache_file = self.stock_collection.get_cache_file_path(stock.symbol, stock.market)
        cache_file = open(stock_cache_file)
        cache_contents = cache_file.read()
        cache_file.close()
        assert hashlib.sha1(cache_contents).\
               hexdigest() == "d304d9962bc0c95ced93fe9826ed12b965d398b5",\
               "cache file has wrong sha1 hexdigest after initial data load"
        # 4. update the db from cache
        self.stock_collection.update_db()
        num_dps = len(session.query(Datapoint).all())
        assert num_dps == 2, 'expected 2 datapoints, found %s' % num_dps
        assert self.dps_are_in_db([dp_A_20120323, dp_A_20120326], to_exclusion=True),\
               'didn\'t find all the db entries we expected'
        # 5. Wait 1 day then update cache and db again
        self.stock_collection.settings.today = datetime.date(year=2012, month=3, day=27)
        self.stock_collection.update_cache()
        cache_file = open(stock_cache_file)
        cache_contents = cache_file.read()
        cache_file.close()
        assert hashlib.sha1(cache_contents).\
               hexdigest() == "033aaa5c736c9f44074dfd4d2657b0c44c406793",\
               "cache file has wrong sha1 hexdigest after first cache update"
        self.stock_collection.update_db()
        num_dps = len(session.query(Datapoint).all())
        assert num_dps == 3, 'expected 3 datapoints, found %s' % num_dps
        assert self.dps_are_in_db([dp_A_20120323, dp_A_20120326, dp_A_20120327], to_exclusion=True),\
               'didn\'t find all the db entries we expected'
        # 6. Add 1 stock
        self.settings.symbols_files = [{u'name':u'NYSE', u'file':u"data/NYSE_test2.txt"}]
        self.stock_collection.load_symbols(self.settings)
        # 7. Update cache and db
        self.stock_collection.update_cache()
        self.stock_collection.update_db()
        num_dps = len(session.query(Datapoint).all())
        assert num_dps == 6, 'expected 6 datapoints, found %s' % num_dps
        expected_dps = [dp_A_20120323, dp_A_20120326, dp_A_20120327, dp_AA_20120323, dp_AA_20120326, dp_AA_20120327]
        assert self.dps_are_in_db(expected_dps, to_exclusion=True),\
               'didn\'t find all the db entries we expected'
        # 8. Wait 1 day, then update cache and db
        self.stock_collection.settings.today = datetime.date(year=2012, month=3, day=28)
        self.stock_collection.update_cache()
        self.stock_collection.update_db()
        num_dps = len(session.query(Datapoint).all())
        assert num_dps == 8, 'expected 8 datapoints, found %s' % num_dps
        assert self.dps_are_in_db([dp_A_20120323, dp_A_20120326, dp_A_20120327, dp_A_20120328,
                                   dp_AA_20120323, dp_AA_20120326, dp_AA_20120327, dp_AA_20120328],\
                                  to_exclusion=True), 'didn\'t find all the db entries we expected'

    def dps_are_in_db(self, dps, to_exclusion=False):
        session = self.Session()
        parsed_dps = []
        existing_dps = []
        for dp in dps:
            parsed_dp = self.stock_collection.parse_csv_line(dp[2])
            parsed_dp['market'] = dp[0]
            parsed_dp['stock'] = dp[1]
            parsed_dps.append(parsed_dp)
        for existing_dp in session.query(Datapoint).all():
            foo = {}
            foo['market'] = existing_dp.stock.market
            foo['stock'] = existing_dp.stock.symbol
            foo['open_val'] = existing_dp.open_val
            foo['high'] = existing_dp.high
            foo['low'] = existing_dp.low
            foo['close'] = existing_dp.close
            foo['volume'] = existing_dp.volume
            foo['adj_close'] = existing_dp.adj_close
            foo['date'] = existing_dp.day.date
            existing_dps.append(foo)
        if to_exclusion:
            for dp in parsed_dps:
                if dp not in existing_dps: return False
            if len(parsed_dps) != len(existing_dps): return False
            return True
        else:
            for dp in parsed_dps:
                if dp not in existing_dps: return False
        return True
