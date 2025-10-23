import sqlite3
import logging
import yaml
import contextlib
from datetime import datetime
from dataclasses import dataclass
import os

from .game.parse import GameRecord

logger = logging.getLogger(__name__)

@dataclass(eq=True, frozen=True)
class RecordPresence:
    text: bool
    image: bool
    exists: bool

class Db:
    def __enter__(self):
        self.con = sqlite3.connect(self.db_location)
        return self.con

    def __exit__(self, _exc_typ, _exc_val, _exc_tb):
        self.con.close()

    def __init__(self, cfg):
        self.db_location = os.path.expanduser(cfg.dat['archives']['db'])
        self.tz = cfg.timezone
        with self as db:
            db.execute("""CREATE TABLE IF NOT EXISTS dat (
                            id         INTEGER,
                            date       DATE     NOT NULL
                                       DEFAULT (DATE('now') ),
                            game       TEXT     NOT NULL,
                            timestamp  DATETIME NOT NULL
                                       DEFAULT (DATETIME('now') ),
                            text_data  TEXT,
                            image_data BLOB,
                            UNIQUE (date, game),
                            PRIMARY KEY (id AUTOINCREMENT));""")

    insert_text_query = (
        'INSERT INTO dat (date, game, timestamp, text_data) '
        'VALUES (:date, :game, :timestamp, :data) '
        'ON CONFLICT (date, game) DO UPDATE SET text_data = excluded.text_data '
        'RETURNING game, text_data, image_data'
    )
    insert_binary_query = (
        'INSERT INTO dat (date, game, timestamp, image_data) '
        'VALUES (:date, :game, :timestamp, :data) '
        'ON CONFLICT (date, game) DO UPDATE SET image_data = excluded.image_data '
        'RETURNING game, text_data, image_data'
    )
    insert_none_query = (
        'INSERT into dat (date, game, timestamp) '
        'VALUES (:date, :game, :timestamp) '
        'RETURNING game, text_data, image_data'
    )
    def save(self, date, game, thing):
        with (self as db, contextlib.closing(db.cursor()) as cur, db):
            info = {
                "date": date,
                "game": game,
                "timestamp": datetime.now(tz=self.tz).isoformat(),
                "data": thing,
            }
            try:
                if isinstance(thing, str):
                    logger.debug("Inserting a string to the database")
                    r = cur.execute(self.insert_text_query, info)
                elif isinstance(thing, bytes):
                    logger.debug("Inserting bytes to the database")
                    r = cur.execute(self.insert_binary_query, info)
                elif thing is None:
                    logger.info("Inserting a blank line to the database")
                    r = cur.execute(self.insert_none_query, info)
                else:
                    logger.error(f"Don't know what to do with {thing}")
                    raise ValueError(f"Don't know what to do with {thing}")
                (game, text, image) = r.fetchone()
            except sqlite3.IntegrityError:
                logger.warning('Cannot insert game - may have already been inserted')
            else:
                return GameRecord(game, text, image)

    load_query = ("SELECT date, game, text_data, image_data FROM dat "
                  "WHERE date = ? AND game = ?")
    def load(self, date, game):
        with (self as db, contextlib.closing(db.cursor()) as cur):
            match cur.execute(self.load_query, (date, game)).fetchone():
                case (_, game, text, image):
                    return GameRecord(game, text, image)
                case None:
                    return GameRecord(game, None, None, False)

    peek_query = ("SELECT text_data IS NOT NULL AS has_text, "
                  "image_data IS NOT NULL AS has_image FROM dat "
                  "WHERE date = ? AND game = ?")
    def peek(self, date, game):
        with (self as db, contextlib.closing(db.cursor()) as cur):
            match cur.execute(self.peek_query, (date, game)).fetchone():
                case (text, image):
                    return RecordPresence(text == 1, image == 1, True)
                case None:
                    return RecordPresence(False, False, False)

    date_query = "SELECT game, text_data, image_data FROM dat WHERE date = ?"
    def load_date(self, date):
        with (self as db, contextlib.closing(db.cursor()) as cur):
            return [
                GameRecord(game, text, image)
                for (game, text, image) in cur.execute(self.date_query, (date,))
            ]

class TextArchiveLoader(yaml.SafeLoader):
    def construct_mapping(self, node):
        pairs = self.construct_pairs(node, deep=True)
        try:
            return dict(pairs)
        except TypeError:
            rv = {}
            for key, value in pairs:
                if isinstance(key, list):
                    key = tuple(key)
                    rv[key] = value
            return rv

TextArchiveLoader.add_constructor('tag:yaml.org,2002:map',
                                  TextArchiveLoader.construct_mapping)

def load_archives(filename):
    with open(filename) as f:
        return yaml.load(f, TextArchiveLoader)

def dump_to_db(filename, selected_date, db):
    for ((game, date), dat) in load_archives(filename).items():
        if selected_date == date:
            with contextlib.suppress(sqlite3.IntegrityError):
                db.save(dat['timestamp'], game, dat['dat'])
