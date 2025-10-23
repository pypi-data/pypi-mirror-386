import textwrap
import math
import logging
import re
from types import SimpleNamespace
from enum import Enum

logger = logging.getLogger(__name__)

class GameParseError(Exception):
    pass

class SuccessMetric(Enum):
    ALWAYS_SUCCEED = "always_succeed"
    LAST_ROW_UNIFORM = "last_row_uniform"
    NOT_SCORE_ZERO = "not_score_zero"

class Reparser:
    config_name = None
    @classmethod
    def from_dict(cls, spec):
        spec.pop("action")
        return cls(**spec)

    def op(self, game):
        pass

class AlternateSuccessMetric(Reparser):
    config_name = "success_metric"
    def __repr__(self):
        return f'{type(self).__qualname__}(metric={self.style.value!r})'
    def __init__(self, metric):
        self.style = SuccessMetric(metric)

    def op(self, game):
        if self.style == SuccessMetric.ALWAYS_SUCCEED:
            game.success = True
        elif self.style == SuccessMetric.NOT_SCORE_ZERO:
            game.success = game.extra_results.score != 0
        elif self.style == SuccessMetric.LAST_ROW_UNIFORM:
            last_row = game.result_rows[-1]
            game.success = last_row == last_row[0] * len(last_row)

class IntegerScoreToSquares(Reparser):
    config_name = "integer_score_to_squares"
    def __repr__(self):
        return f'{type(self).__qualname__}(columns={self.cols!r})'

    def __init__(self, columns=8):
        self.cols = columns

    def op(self, game):
        game.cols = self.cols
        score = game.extra_results.score
        game.rows = math.ceil(score / self.cols)
        cells = game.rows * self.cols
        game.result_rows = textwrap.wrap(
            (chr(0x1F7E5) * score).ljust(cells, chr(0x2B1C)),
            self.cols)

def _parse_types(thing):
    if thing == 'int': return int
    elif thing == 'float': return float
    elif thing == 'str': return str
    else:
        logger.warn(f'Unknown item type {thing} given, defaulting to str')
        return str

class ParseAndReformatCaption(Reparser):
    config_name = "reformat_caption"
    def __repr__(self):
        return (f'{type(self).__qualname__}(regexp={self.regexp!r}, '
                f'capture_groups={self.capture_groups!r}, '
                f'format_string={self.format_string!r})')

    def __init__(self, regexp, capture_groups, format_string=None, types=None):
        self.format_string = format_string
        self.regexp = re.compile(regexp)
        self.capture_groups = capture_groups
        self.types = ([str] * len(self.capture_groups)) if types is None else [_parse_types(i) for i in types]
    @classmethod
    def from_dict(cls, spec):
        return cls(
            regexp=spec.get("caption_regexp"),
            capture_groups=spec["capture"],
            format_string=spec.get("format_string"),
            types=spec.get('types'),)

    def op(self, game):
        default_string = f"{game.game_name.title()} {{puzzle_number}}"
        if dat := re.search(self.regexp, game.caption):
            captures = {i: dat.group(n + 1) for n, i in enumerate(self.capture_groups)}
        else:
            raise GameParseError
        for t, (k, v) in zip(self.types, captures.items()):
            captures[k] = t(v)
        game.extra_results = SimpleNamespace(**captures)
        game.caption = (self.format_string or default_string).format(**captures)

class Hexcodle(Reparser):
    config_name = "hexcodle"
    def op(self, game):
        if dat := re.search(
                '^I got Hexcodle #([0-9]+) in ([0-9])! Score: ([0-9]+)%', game.caption):
            game.caption = f'Hexcodle {dat.group(1)} {dat.group(2)}/5 @ {dat.group(3)}%'
            game.success = True
        elif dat := re.search(
                '^I didn\'t get Hexcodle #([0-9]+) :\\( Score: ([0-9]+)%', game.caption):
            game.caption = f'Hexcodle {dat.group(1)} X/5 @ {dat.group(2)}%'
            game.success = False
        else:
            raise GameParseError
        return game
