from enum import Enum
import pytesseract
import re
import io
import os
from PIL import Image
from datetime import datetime
import subprocess
import logging

from .res import Audio

logger = logging.getLogger(__name__)

class DetectionType(Enum):
    TEXT = "text"
    IMAGE = "image"

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

class Game:
    def __init__(self, db):
        self.date = datetime.today().strftime("%Y-%m-%d")
        self.gui = None
        self.db = db
        self.result = None

    def log(self, text):
        if self.gui is not None:
            self.gui.new_status(text)
        else:
            logger.info(text)

    @classmethod
    def from_dict(cls, d, db):
        inst = cls(db)
        dat = {
            "detection": DetectionType.TEXT,
            "refresh_hour": 0,
            "short_name": d['name'].lower(),
            "name": None,
            "required": True,
            "target": None,
            "text_target": None,
            "display_row": 0,
        } | d
        inst.name = dat["name"]
        inst.required = dat["required"]
        inst.detection = DetectionType(dat["detection"])
        inst.refresh_hour = dat["refresh_hour"]
        inst.display_row = dat["display_row"]
        inst.short_name = dat.get("short_name", dat["name"].lower())
        inst.out_filename = f'{inst.short_name}-{inst.date}'
        inst.target = re.compile(dat['target'] if dat.get('target') else "^" + dat["name"])
        inst.text_target = re.compile(dat['text_target'] if dat.get('text_target') else inst.target)
        if not (inst.name and inst.target):
            raise ValueError("name and target must be defined.")
        inst.result = inst.db.load(inst.date, inst.short_name)
        return inst

    def __repr__(self):
        return "<{class_name} {game_name}{collectedp}>".format(
            class_name=type(self).__qualname__,
            game_name=str(self.name),
            collectedp=" collected" if self.collectedp() else "",
        )

    def eligiblep(self):
        return self.refresh_hour <= datetime.now().hour

    def collectedp(self):
        if self.detection == DetectionType.TEXT:
            return self.db.peek(self.date, self.short_name).text == 1
        elif self.detection == DetectionType.IMAGE:
            dat = self.db.peek(self.date, self.short_name)
            return dat.text == 1 and dat.image == 1

    def status(self):
        dat = self.db.peek(self.date, self.short_name)
        has_image_but_no_text = dat.image == 1 and dat.text == 0
        if self.collectedp():
            return GameStatus.COLLECTED
        elif not self.eligiblep():
            return GameStatus.UNELIGIBLE
        elif has_image_but_no_text:
            return GameStatus.PARTIALLY_COLLECTED
        elif self.required:
            return GameStatus.UNCOLLECTED
        else:
            return GameStatus.OPTIONAL

    def status_str(self):
        if self.result.text is not None:
            return self.result.text.splitlines()[self.display_row]
        else:
            return self.status().as_str()

    def save_text_to_file(self, thing):
        with open(self.out_filename + '.txt', 'w') as f:
            f.write("\n".join(line for line in thing.splitlines()
                              if not line.startswith("http")))
            f.write("\n")

    def save_to_db(self, thing):
        if isinstance(thing, str):
            r = self.db.save(self.date, self.short_name,
                         "\n".join(line for line in thing.splitlines()
                                   if not line.startswith("http")))
        elif isinstance(thing, bytes): # image
            r = self.db.save(self.date, self.short_name, thing)
        else:
            raise ValueError(f"Don't know what to do with {thing} on saving")
        return r

    def matches(self, thing):
        if isinstance(thing, str) and self.detection == DetectionType.TEXT:
            return self.target.search(thing)
        elif isinstance(thing, str) and self.detection == DetectionType.IMAGE:
            return self.text_target.search(thing)
        elif isinstance(thing, Image.Image) and self.short_name == 'celtix':
            return self.target.search(
                pytesseract.image_to_string(thing.crop((0, 0, 222, 74))))
        elif isinstance(thing, Image.Image):
            return self.target.search(pytesseract.image_to_string(thing))
        else:
            raise ValueError(f"Don't know what to do with {thing} on matching")

    def wants(self) -> GameAccepts:
        self.result = self.db.load(self.date, self.short_name)
        if self.collectedp() or not self.eligiblep():
            return GameAccepts.NONE
        elif self.detection == DetectionType.TEXT or (
                self.detection == DetectionType.IMAGE
                and self.result.image is not None):
            return GameAccepts.TEXT
        elif self.detection == DetectionType.IMAGE and self.result.image is None:
            return GameAccepts.IMAGE
        else:
            logger.error('Unreachable want!')

    def collect_if_match(self, thing):
        if self.wants() == GameAccepts.NONE:
            return None
        elif (self.wants() == GameAccepts.TEXT
              and isinstance(thing, str)
              and self.matches(thing)):
            self.save_text_to_file(thing)
            self.result = self.save_to_db(thing)
            self.log(f'Collected text of {self.name}')
            Audio.COMPLETE.play()
        elif (self.wants() == GameAccepts.IMAGE
              and isinstance(thing, Image.Image)
              and self.matches(thing)):
            image_filename = self.out_filename + ".png"
            thing.save(image_filename)
            subprocess.run(['pngcrush', '-ow', image_filename])
            with open(image_filename, 'rb') as f:
                self.result = self.save_to_db(f.read())
            Audio.READY_FOR_TEXT.play()
            self.log(f'Collected image of {self.name}')
        else:
            # logger.error(f'Item {self} does not match')
            # logger.error(f'{self.wants()=}')
            # logger.error(f'{self.matches(thing)=}')
            # logger.error(f'{type(thing)=}')
            return None
        return self

class CollectionStatus(Enum):
    INCOMPLETE = 'incomplete'
    COMPLETE_FOR_NOW = 'complete-for-now'
    COMPLETE = 'complete'

class GameCollection:
    def __init__(self, collection, db):
        self.collection = [Game.from_dict(i, db) for i in collection]

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

def play_sound(path):
    subprocess.Popen(["paplay", os.path.expanduser(path)])

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
