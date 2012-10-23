# Stock Data Cacher

## Overview

Stock Data Cacher (hereafter SDC) creates and updates caches of raw data from Yahoo! Financials' stocks data. Yahoo! provides the data in csv format. This program caches the data in a PostgreSQL database.

It is assumed you have independently obtained permission from Yahoo! to use their data service, and your compliance with the Yahoo! Financials Terms of Service is your own responsibility. Stock symbols need to be obtained separately, and again you are responsible for providing your own list of stock symbols. If you obtain stock symbols from third party data providers, your compliance with their terms of service is your own responsibility.

Stock Data Cacher consists of a primary module (StockCollection.py) and a few helper files like a settings file and a sample driver main.py.

## Limitations

There are quite a lot of limitations, and this should only be considered a PoC. Noteworthy limitations include and are not limited to:

1. Not all symbols are cached. SDC requires a list of symbols so it knows what to fetch. I am not aware of a list of symbols Yahoo! uses, so I obtained them from eoddata (see instructions below). The symbols on eoddata mostly correspond to the ones on Yahoo! but not completely. So there's a hackish function filtering out known inconsistenceies (see function validate_symbol in StockCollection.py).
2. SDC does not handle retroactive adjustments in adj_close very well.
3. The included tests have abysmal coverage, are slow, terribly composed, and should be taken out back and shot.

## Optimisations

## Using

SDC is usable as a module, but a rudimentary command line driver is provided in main.py. Run `python main.py --help` for a brief overview of capabilities.

Before doing anything else, go through `settings.py` and adapt it to your needs. The knobs and levers are reasonably well documented in the file itself.

You will also need to ensure that all requirements are met. I recommend you run SDC in a virtualenv. A requirements.txt is included for the benefit of pip.

### SDC initialisation

SDC needs a list of stock symbols before it can do anything. I have been using data from [eoddata](http://www.eoddata.com/). You will need to register there and obtain the raw list of symbols yourself as I cannot distribute that data. The subsequent file must be placed in the data/ folder and added to the symbols_files variable in settings.py. Your compliance with eoddata's Terms of Use is your own responsibility. You may also hand-craft a symbols file; the format is quite simple. A header row is discarded, and after that it is plain text with whitespace separation, like:

`Symbol  Description
A       Agilent Technologies`

The database needs to be initialised. Assuming you have created a PostgreSQL database and user for SDC, plug those in the `db_url` variable in the settings file and run `python main.py --recreate-db`. This is a **DESTRUCTIVE** command. It will wipe the db and initialise a blank one in its stead.

### Seeding

`python main.py --update` will seed the database.

### Maintaining/Updating

Rune `python main.py --update` at whatever interval suits you.

### tests

The tests require that the data/ folder contains sample data. You will have to handcraft this yourself. At this stage it's simpler to just not run the tests. See the Future section below.

## Future

1. Investigate shifting to Pandas for persistence
2. There's optimisations which currently are dead, such as `assume_datapoints_unique` in the settings file. I might reimplement those.
3. Retroactive adj_close changes should be handled. Maybe a [Point in Time Architecture](http://www.simple-talk.com/sql/database-administration/database-design-a-point-in-time-architecture/) is in order here, but it feels like overkill.
4. The tests are currently dependent on some sample data from actual stock data. I cannot redistribute this so it's probably really annoying to anyone who wants to run the tests; they'd have to actuall red the tests, infer what sample data is required, and hand craft it. This can surely be done better.

## License

The file `StockCollection.py` is licensed under the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html) license. Everything else is public domain; for countries without public domain legal status, all files other than `StockCollection.py` may be considered to have rights waived.

I can be contacted at josef@josefassad.com