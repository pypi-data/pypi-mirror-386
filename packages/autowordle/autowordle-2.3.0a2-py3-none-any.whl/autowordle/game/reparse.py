import textwrap
import math
import logging
import re
from types import SimpleNamespace

from .parse import GameParser, ParsedGame

logger = logging.getLogger(__name__)

class GameParseError(Exception):
    pass

class Reparser:
    def op(self, game):
        pass

class AlwaysSucceed(Reparser):
    def op(self, game):
        game.success = True

class AlternateSuccessMetric(Reparser):
    def op(self, game):
        last_row = game.result_rows[-1]
        game.success = last_row == last_row[0] * len(last_row)

class IntegerScoreToSquares(Reparser):
    def __init__(self, *, cols=8):
        self.cols = cols

    def op(self, game):
        game.cols = self.cols
        score = int(game.extra_results.score)
        game.rows = math.ceil(score / self.cols)
        cells = game.rows * self.cols
        game.result_rows = textwrap.wrap(
            (chr(0x1F7E5) * score).ljust(cells, chr(0x2B1C)),
            self.cols)

class ParseAndReformatCaption(Reparser):
    def __init__(self, regexp, capture_groups, format_string=None):
        self.format_string = format_string
        if isinstance(capture_groups, list):
            self.regexp = re.compile(regexp)
            self.capture_groups = capture_groups
        elif isinstance(capture_groups, dict):
            self.regexp = None
            self.capture_groups = {k: re.compile(v) for k, v in capture_groups.items()}
        else:
            raise ValueError(f'{capture_groups} must be a list or a dict')

    def op(self, game):
        default_string = f"{game.game_name.title()} {{puzzle_number}}"
        if isinstance(self.capture_groups, list):
            if dat := re.search(self.regexp, game.caption):
                captures = {i: dat.group(n + 1) for n, i in enumerate(self.capture_groups)}
            else:
                raise GameParseError
        elif isinstance(self.capture_groups, dict):
            captures = {
                k: v.search(game.caption).group(1) for k, v in self.capture_groups.items()}
        else:
            raise ValueError(f'{self.capture_groups} must be a list or a dict')
        game.extra_results = SimpleNamespace(**captures)
        game.caption = (self.format_string or default_string).format(**captures)

GameParser.define_reparse_function(
    'celtix',
    ParseAndReformatCaption('Celtix ([0-9]+) using ([0-9]+) wall',
                            ["puzzle_number", "score"],),
    IntegerScoreToSquares(cols=8),
    AlwaysSucceed(),
)

GameParser.define_reparse_function(
    'connections',
    ParseAndReformatCaption('Puzzle #([0-9]+)', ["puzzle_number"]),
    AlternateSuccessMetric()
)

GameParser.define_reparse_function(
    'kotoba',
    ParseAndReformatCaption(
        '([0-9]+) (1?[0-9X])+/12(\\?)?',
        ["puzzle_number", "guesses", "modifiers"],
        "言葉で遊ぼう\n{puzzle_number} {guesses}/12{modifiers}",)
)

GameParser.define_reparse_function(
    'diffle',
    ParseAndReformatCaption("([0-9]+) words / ([0-9]+) letters",
                            ["words", "letters"],
                            "Diffle {words}/{letters}",),
    AlwaysSucceed()
)

GameParser.define_reparse_function(
    'redactle',
    ParseAndReformatCaption(
        r'[#Q]([0-9]+) in ([0-9]+) guess(?:es)? with an accuracy of ([0-9]+\.[0-9]+)%',
        ["puzzle_number", "guesses", "accuracy"])
)

@GameParser.reparser_for('hexcodle')
def reparse_hexcodle(game: ParsedGame) -> ParsedGame:
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
