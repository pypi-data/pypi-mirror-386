from enum import Enum
import re
import io
import os
from PIL import Image
from datetime import datetime
import subprocess
import logging
import tempfile

from .res import Audio
from .game import Detector, DetectionType

logger = logging.getLogger(__name__)

class GameAccepts(Enum):
    NONE = "none"
    TEXT = "text"
    IMAGE = "image"

class GameStatus(Enum):
    OPTIONAL = 'optional'
    PARTIALLY_COLLECTED = 'partially_collected'
    COLLECTED = 'collected'
    UNCOLLECTED = 'uncollected'
    UNELIGIBLE = 'uneligible'
    def as_str(self):
        if self == GameStatus.OPTIONAL:
            return 'Optional'
        elif self == GameStatus.PARTIALLY_COLLECTED:
            return 'Awaiting text'
        elif self == GameStatus.COLLECTED:
            return 'Collected'
        elif self == GameStatus.UNCOLLECTED:
            return 'Uncollected'
        elif self == GameStatus.UNELIGIBLE:
            return 'Ineligible'

class Collector:
    def __init__(self, spec, db, date):
        self.date = date.strftime("%Y-%m-%d")
        self.gui = None
        self.db = db
        self.detector = Detector(spec)
        self.name = spec.name
        self.display_row = spec.display_row
        self.refresh_hour = spec.refresh_hour
        self.short_name = self.detector.short_name
        self.out_filename = f'{self.detector.short_name}-{self.date}'
        self.result = self.db.load(self.date, self.short_name)

    def log(self, text):
        if self.gui is not None:
            self.gui.new_status(text)
        else:
            logger.info(text)

    def __repr__(self):
        return "<{class_name} {game_name}{collectedp}>".format(
            class_name=type(self).__qualname__,
            game_name=str(self.name),
            collectedp=" collected" if self.collectedp() else "",
        )

    def eligiblep(self):
        return self.refresh_hour <= datetime.now().hour

    def collectedp(self):
        if self.detector.detection == DetectionType.TEXT:
            return self.result.text is not None
        elif self.detector.detection == DetectionType.IMAGE:
            return self.result.text is not None and self.result.image is not None

    def status(self):
        has_image_but_no_text = self.result.text is None and self.result.image is not None
        if self.collectedp():
            return GameStatus.COLLECTED
        elif not self.eligiblep():
            return GameStatus.UNELIGIBLE
        elif has_image_but_no_text:
            return GameStatus.PARTIALLY_COLLECTED
        else:
            return GameStatus.UNCOLLECTED
        # else:
        #     return GameStatus.OPTIONAL

    def status_str(self):
        if self.result.text is not None:
            return self.result.text.splitlines()[self.display_row]
        else:
            return self.status().as_str()

    def save_to_db(self, thing):
        if isinstance(thing, str):
            r = self.db.save(self.date, self.short_name,
                         "\n".join(line for line in thing.splitlines()
                                   if not line.startswith("http")))
        elif isinstance(thing, bytes): # image
            r = self.db.save(self.date, self.short_name, thing)
        else:
            raise ValueError(f"Don't know what to do with {thing} on saving")
        self.result = r
        return r

    def wants(self) -> GameAccepts:
        match (self.status(), self.detector.detection):
            case (GameStatus.COLLECTED | GameStatus.UNELIGIBLE, _):
                return GameAccepts.NONE
            case ((GameStatus.UNCOLLECTED, DetectionType.TEXT)
                  | (GameStatus.PARTIALLY_COLLECTED, DetectionType.IMAGE)):
                return GameAccepts.TEXT
            case (GameStatus.UNCOLLECTED, DetectionType.IMAGE):
                return GameAccepts.IMAGE
            case _:
                logger.error('Unreachable want!')
                raise RuntimeError(f'{self} has an unreachable want')

    def collect_if_match(self, thing):
        if self.wants() == GameAccepts.NONE:
            return None
        elif (self.wants() == GameAccepts.TEXT
              and isinstance(thing, str)
              and self.detector.matches(thing)):
            self.result = self.save_to_db(thing)
            self.log(f'Collected text of {self.name}')
            Audio.COMPLETE.play()
        elif (self.wants() == GameAccepts.IMAGE
              and isinstance(thing, Image.Image)
              and self.detector.matches(thing)):
            self.result = self.save_to_db(compress_image(thing))
            self.log(f'Collected image of {self.name}')
            Audio.READY_FOR_TEXT.play()
        else:
            return None
        return self

def compress_image(image):
    with tempfile.NamedTemporaryFile(prefix="autowordle_", suffix='.png', mode='wb',
                                     delete_on_close=False) as tmpfile:
        image.save(tmpfile)
        with subprocess.Popen(['pngcrush', tmpfile.name, '/dev/stdout'],
                              stdout=subprocess.PIPE) as proc:
            return proc.stdout.read()

class CollectionStatus(Enum):
    INCOMPLETE = 'incomplete'
    COMPLETE_FOR_NOW = 'complete-for-now'
    COMPLETE = 'complete'

class GameCollection:
    def __init__(self, collection, db, date):
        self.collection = [Collector(i, db, date) for i in collection]

    def __repr__(self):
        return f"<{type(self).__qualname__}, {len(self.collection)} entries>"

    def inject_gui(self, gui):
        for i in self.collection:
            i.gui = gui

    def eligible(self):
        return [x for x in self.collection if x.eligiblep()]

    def status(self):
        if all(x.collectedp() for x in self.collection):
            return CollectionStatus.COMPLETE
        elif all(x.collectedp() for x in self.eligible()):
            return CollectionStatus.COMPLETE_FOR_NOW
        else:
            return CollectionStatus.INCOMPLETE

    def get(self, game_name):
        return next(x for x in self.collection if x.name == game_name)

    def find_matching_game(self, thing):
        for i in self.eligible():
            if res := i.collect_if_match(thing):
                return res
        return None

def clipboard():
    if re.search(
            "image/",
            subprocess.run(
                ["xclip", "-sel", "c", "-target", "TARGETS", "-out"],
                capture_output=True).stdout.decode("UTF-8")):
        return Image.open(
            io.BytesIO(
                subprocess.run(
                    ["xclip", "-sel", "c", "-target", "image/png", "-out"],
                    capture_output=True).stdout))
    else:
        return subprocess.run(
            ["xclip", "-sel", "c", "-out"],
            capture_output=True).stdout.decode("UTF-8")
