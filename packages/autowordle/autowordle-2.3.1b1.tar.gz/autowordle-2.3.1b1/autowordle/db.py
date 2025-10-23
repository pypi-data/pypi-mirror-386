import sqlite3
import logging
import contextlib
from datetime import datetime
from dataclasses import dataclass
import os
import pytz

from . import res

logger = logging.getLogger(__name__)
UTC = pytz.timezone('Etc/Utc')

@dataclass(eq=True, frozen=True)
class GameRecord:
    game: str
    text: str | None
    image: bytes | None
    timestamp: datetime | None = None
    present: bool = True

    def __repr__(self):
        image = (f"<{len(self.image)} bytes>"
                 if self.image and len(self.image) > 100
                 else self.image)
        return (f"{self.__class__.__qualname__}(game={self.game!r}, "
                f"text={self.text!r}, image={image}, datetime={self.timestamp!r}, "
                f"present={self.present})")

    def __str__(self):
        if self.present:
            return "<{class_name} {game}, text:{text}, image={image}>".format(
                class_name=self.__class__.__qualname__,
                game=f'{self.game!r}',
                text=f"'{self.text.splitlines()[0][:20]}...'" if self.text else 'None',
                image=f"<{len(self.image)} bytes>" if self.image else 'None',
            )
        else:
            return self.__repr__()

class Db:
    def __enter__(self):
        self.con = sqlite3.connect(self.db_location)
        return self.con

    def __exit__(self, _exc_typ, _exc_val, _exc_tb):
        self.con.close()

    def __init__(self, cfg):
        self.db_location = os.path.expanduser(cfg.dat['archives']['db'])
        self.tz = cfg.timezone
        with self as db, open(res.file_res('schema.sql')) as f:
            schema = f.read()
            db.executescript(schema)

    insert_text_query = (
        'INSERT INTO dat (date, game, timestamp, timezone, text_data) '
        'VALUES (:date, :game, :timestamp, :timezone, :data) '
        'ON CONFLICT (date, game) DO UPDATE SET text_data = excluded.text_data '
        'RETURNING game, text_data, image_data'
    )
    insert_binary_query = (
        'INSERT INTO dat (date, game, timestamp, timezone, image_data) '
        'VALUES (:date, :game, :timestamp, :timezone, :data) '
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
            now = datetime.now(tz=UTC)
            info = {"date": date, "game": game, "timezone": str(self.tz),
                    "timestamp": now.astimezone(UTC).isoformat().replace('+00:00', 'Z'),
                    "data": thing}
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
                return GameRecord(game, text, image, now)

    newimg_query = "INSERT INTO outimgs (gentime, timezone, date, hash) VALUES (?, ?, ?, ?);"
    def record_generated_image(self, date, filehash):
        with (self as db, contextlib.closing(db.cursor()) as cur, db):
            cur.execute(self.newimg_query,
                        (datetime.now(tz=UTC).isoformat(), str(self.tz),
                         date, filehash))

    latest_genimg_query = "SELECT max(gentime) FROM outimgs WHERE date < date('now');"
    def latest_generated_image(self):
        with (self as db, contextlib.closing(db.cursor()) as cur):
            latest = cur.execute(self.latest_genimg_query).fetchone()
            return datetime.fromisoformat(latest[0] or "2000-01-01T00:00:00+00:00").astimezone(self.tz)

    load_query = ("SELECT date, timestamp, timezone, game, text_data, image_data FROM dat "
                  "WHERE date = ? AND game = ?")
    def load(self, date, game):
        with (self as db, contextlib.closing(db.cursor()) as cur):
            match cur.execute(self.load_query, (date, game)).fetchone():
                case (_, timestamp, timezone, game, text, image):
                    return GameRecord(game, text, image,
                                      datetime.fromisoformat(timestamp).astimezone(self.tz))
                case None:
                    return GameRecord(game, None, None, None, False)

    date_query = "SELECT game, timestamp, text_data, image_data FROM dat WHERE date = ?"
    def load_date(self, date):
        with (self as db, contextlib.closing(db.cursor()) as cur):
            return [
                GameRecord(game, text, image,
                           datetime.fromisoformat(timestamp).replace('+00:00', 'Z'))
                for (game, timestamp, text, image) in cur.execute(self.date_query, (date,))
            ]
