import logging
import os.path
import sqlite3
from array import array
from datetime import datetime
from typing import Any, Literal

from roboquant.asset import deserialize_to_asset, Asset
from roboquant.event import Bar, PriceItem, Quote
from roboquant.event import Event
from roboquant.timeframe import Timeframe
from roboquant.feeds.feed import Feed

logger = logging.getLogger(__name__)


class SQLFeed(Feed):
    """SQLFeed supports recording price-items from another feed and then play them back during a run.
    There is support for Bars and Quotes. It is also possible to append values to an existing database.

    Under the hood, the data is stored in an SQLite database. The database schema is created automatically when
    the first item is recorded. The database schema is different for Bars and Quotes, so you can only store
    one type of price-items in a single database.

    Please be aware that databases can become very large if using high frequent market data and long periods.
    """

    # Used SQL statements in this class
    _sql_select_all = "SELECT * from prices order by Date"
    _sql_select_by_date = "SELECT * from prices where Date >= ? and Date <= ? order by Date"
    _sql_select_timeframe = "SELECT min(Date), max(Date) from prices"
    _sql_count_items = "SELECT count(*) from prices"
    _sql_select_assets = "SELECT DISTINCT asset from prices"
    _sql_drop_table = "DROP TABLE IF EXISTS prices"
    _sql_create_bar_table = "CREATE TABLE IF NOT EXISTS prices(date, asset, open, high, low, close, volume, frequency)"
    _sql_create_quote_table = "CREATE TABLE IF NOT EXISTS prices(date, asset, ap, av, bp, bv)"
    _sql_insert_bar = "INSERT into prices VALUES(?,?,?,?,?,?,?,?)"
    _sql_insert_quote = "INSERT into prices VALUES(?,?,?,?,?,?)"
    _sql_create_index = "CREATE INDEX IF NOT EXISTS date_idx ON prices(date)"

    def __init__(self, db_file, price_type: Literal["bar", "quote"] = "bar") -> None:
        super().__init__()
        self.db_file = db_file
        self.price_type = price_type
        self.is_bar = price_type == "bar"

    def exists(self) -> bool:
        """Check if the database file exists"""
        return os.path.exists(self.db_file)

    def create_index(self):
        """Create an index on the date column. The database will become larger. But the performance will improve
        when querying data for specific timeframes, for example, in the case of a walk-forward back test.
        If you benefit from this index, best to invoke this method after all the data has been recorded.
        """
        with sqlite3.connect(self.db_file) as con:
            con.execute(SQLFeed._sql_create_index)
            con.commit()

    def number_items(self) -> int:
        """Return the number of price-items in the database"""
        with sqlite3.connect(self.db_file) as con:
            result = con.execute(SQLFeed._sql_count_items).fetchall()
            con.commit()
            row = result[0]
            return row[0]

    def timeframe(self) -> Timeframe:
        """Return the timeframe of the data in the database.
        If no data is found, it will return `Timeframe.EMPTY`.
        """
        with sqlite3.connect(self.db_file) as con:
            result = con.execute(SQLFeed._sql_select_timeframe).fetchall()
            con.commit()
            row = result[0]
            if row[0]:
                return Timeframe.fromisoformat(row[0], row[1], True)
            return Timeframe.EMPTY

    def assets(self) -> list[Asset]:
        """Return all the assets in the database"""
        with sqlite3.connect(self.db_file) as con:
            result = con.execute(SQLFeed._sql_select_assets).fetchall()
            con.commit()
            assets = {deserialize_to_asset(columns[0]) for columns in result}
            return list(assets)

    def _get_item(self, row: list[Any]) -> PriceItem:
        """Get a PriceItem from a row in the database"""
        asset_str = row[1]
        asset = deserialize_to_asset(asset_str)
        if self.is_bar:
            prices = row[2:7]
            freq = row[7]
            return Bar(asset, array("f", prices), freq)
        else:
            prices = row[2:6]
            return Quote(asset, array("f", prices))

    def play(self, timeframe: Timeframe | None = None):
        """Play back the data in the database to the channel"""
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            t_old = ""
            items = []
            result = (
                cur.execute(SQLFeed._sql_select_by_date, [timeframe.start.isoformat(), timeframe.end.isoformat()])
                if timeframe
                else cur.execute(SQLFeed._sql_select_all)
            )

            for row in result:
                t = row[0]
                assert t >= t_old, f"{t} t_old"
                if t != t_old:
                    if items:
                        dt = datetime.fromisoformat(t_old)
                        event = Event(dt, items)
                        yield event
                        items = []
                    t_old = t

                item = self._get_item(row)
                items.append(item)

        # send the remainders
        if items:
            dt = datetime.fromisoformat(t_old)
            event = Event(dt, items)
            yield event

    def record(self, feed: Feed, timeframe: Timeframe | None = None, append: bool = False, batch_size: int = 10_000):
        """Record another feed into this SQLite database.
        It supports Bars and Quotes, other types of price-items are ignored."""
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()

            create_sql = SQLFeed._sql_create_bar_table if self.is_bar else SQLFeed._sql_create_quote_table
            insert_sql = SQLFeed._sql_insert_bar if self.is_bar else SQLFeed._sql_insert_quote

            if not append:
                cur.execute(SQLFeed._sql_drop_table)

            cur.execute(create_sql)
            price_type = self.price_type

            data = []
            for event in feed.play(timeframe):
                t = event.time
                for item in event.items:
                    if isinstance(item, Bar) and price_type == "bar":
                        elem = (t.isoformat(), item.asset.serialize(), *item.ohlcv, item.frequency)
                        data.append(elem)
                    elif isinstance(item, Quote) and price_type == "quote":
                        elem = (t.isoformat(), item.asset.serialize(), *item.data)
                        data.append(elem)
                if len(data) >= batch_size:
                    cur.executemany(insert_sql, data)
                    data = []

            if data:
                cur.executemany(insert_sql, data)

            con.commit()

    def __repr__(self) -> str:
        return f"SQLFeed(path={self.db_file} is_bar={self.is_bar})"
