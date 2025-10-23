import pytesseract
import re
from enum import Enum
from PIL import Image
from dataclasses import dataclass, field
import logging
import typing

from .reparse import Reparser

logger = logging.getLogger(__name__)

class DetectionType(Enum):
    TEXT = "text"
    IMAGE = "image"

@dataclass
class GameDefinition:
    code: str
    name: str
    target: re.Pattern
    text_target: re.Pattern | None
    window_title: str
    detection: DetectionType = DetectionType.TEXT
    refresh_hour: int = 0
    required: bool = True
    display_row: int = 0
    crop: typing.Optional[typing.Tuple[int, int, int, int]] = None
    reparse_actions: list[Reparser] = field(default_factory=list)

    def __init__(self, spec):
        if 'name' not in spec:
            raise ValueError('Must provide at least the name of the game.')
        dat = {
            "detection": DetectionType.TEXT,
            "refresh_hour": 0,
            "short_name": spec['name'].lower(),
            "name": None,
            "required": True,
            "target": "^" + spec["name"],
            "text_target": None,
            "display_row": 0,
            "crop": None,
            "reparse_actions": [],
            "window_title": spec['name'],
        } | spec
        self.window_title = dat['window_title']
        self.name = dat["name"]
        self.required = dat["required"]
        self.detection = DetectionType(dat["detection"])
        self.refresh_hour = dat["refresh_hour"]
        self.display_row = dat["display_row"]
        self.code = dat["short_name"]
        self.target = re.compile(dat['target'])
        self.text_target = re.compile(dat['text_target'] or self.target)
        match dat['crop']:
            case [x, y, w, h]: self.crop = (x, y, w, h)
            case None | []: self.crop = None
            case _:
                raise ValueError('Invalid crop spec: '
                                 'must be missing or an array of four integers.')

        self.reparse_actions = list()
        subclasses = Reparser.__subclasses__()
        for i in dat["reparse_actions"]:
            try:
                self.reparse_actions.append(
                    next(c for c in subclasses
                         if c.config_name == i["action"]).from_dict(i)
                )
            except StopIteration as e:
                raise ValueError(f'Unknown reparser {i["action"]}') from e
        if not re.fullmatch('^[a-z]+$', self.code):
            raise ValueError("A game code can only consist of lowercase letters.")
        if not (self.name and self.target):
            raise ValueError("name and target must be defined.")

class Detector:
    def __init__(self, spec):
        self.name = spec.name
        self.short_name = spec.code
        self.detection = spec.detection
        self.target = spec.target
        self.text_target = spec.text_target
        self.crop = spec.crop

    def __str__(self):
        return "<{class_} {short_name} ({name}) {target}>".format(
            class_=self.__class__.__qualname__,
            short_name=self.short_name,
            name=self.name,
            target=self.target,
        )

    def matches(self, thing):
        if isinstance(thing, str) and self.detection == DetectionType.TEXT:
            return self.target.search(thing)
        elif isinstance(thing, str) and self.detection == DetectionType.IMAGE:
            return self.text_target.search(thing)
        elif isinstance(thing, Image.Image) and self.crop is not None:
            return self.target.search(
                pytesseract.image_to_string(thing.crop(self.crop)))
        elif isinstance(thing, Image.Image):
            return self.target.search(pytesseract.image_to_string(thing))
        else:
            raise ValueError(f"Don't know what to do with {thing} on matching")
