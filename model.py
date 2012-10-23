#!/usr/bin/env python

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation, clear_mappers

db_url=u"postgresql://stocksie:stocksie@localhost/stocksie"

metadata = MetaData(create_engine(db_url))

stock_table = Table(
    'stock', metadata,
    Column('id', Integer, primary_key=True),
    Column('symbol', Unicode(20), nullable=False, index=True, unique=True),
    Column('name', Unicode(100), nullable=True),
    Column('market', Unicode(20), nullable=True),
    Column('last_cache_update', Date),
    Column('last_db_update', Date),
    UniqueConstraint('symbol', 'market'))

day_table = Table(
    'day', metadata,
    Column('id', Integer, primary_key=True),
    Column('date', Date, unique=True, index=True))

datapoint_table = Table(
    'datapoint', metadata,
    Column('id', Integer, primary_key=True),
    Column('stock_id', None, ForeignKey('stock.id')),
    Column('day_id', None, ForeignKey('day.id')),
    Column('open_val', Integer),
    Column('high', Integer),
    Column('low', Integer),
    Column('close', Integer),
    Column('volume', Integer),
    Column('adj_close', Integer),
    UniqueConstraint('stock_id', 'day_id'))

def init_model(engine):
    metadata.create_all()


class Datapoint(object):
    def __init__(self, stock_id, day_id, open_val,
                 high, low, close, volume, adj_close):
        self.stock_id  = stock_id
        self.day_id    = day_id
        self.open_val  = open_val
        self.high      = high
        self.low       = low
        self.close     = close
        self.volume    = volume
        self.adj_close = adj_close

    def __repr__(self):
        foo = str(self.stock_id) + " " + str(self.day_id)
        return u'<Datapoint %s>' % foo


class Stock(object):

    def __init__(self, symbol, name, market):
        self.name              = name
        self.symbol            = symbol
        self.market            = market
        self.last_cache_update = None
        self.last_db_update    = None

    def __repr__(self):
        return u'<Stock: %s (%s)>' % (self.symbol, self.market)


class Day(object):
    def __init__(self, date):
        self.date   = date
    def __repr__(self):
        return u'<Day: %s>' % self.date


clear_mappers()

mapper(Datapoint, datapoint_table)
mapper(Day, day_table,
       properties=dict(datapoints=relation(Datapoint, backref='day')))
mapper(Stock, stock_table,
       properties=dict(datapoints=relation(Datapoint, backref='stock')))
