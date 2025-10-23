import re
import os
import math
import textwrap
import logging
from dataclasses import dataclass
import typing

from .res import CHAR_TO_FILE

logger = logging.getLogger(__name__)

@dataclass(eq=True, frozen=True)
class GameRecord:
    game: str
    text: str | None
    image: bytes | None
    present: bool = True

    def __repr__(self):
        image = (f"<{len(self.image)} bytes>"
                 if self.image and len(self.image) > 100
                 else self.image)
        return (f"{self.__class__.__qualname__}(game={self.game!r}, "
                f"text={self.text!r}, image={image}, present={self.present})")

    def __str__(self):
        if self.present:
            return "<{class_name} {game}, text:{text}, image={image}>".format(
                class_name=self.__class__.__qualname__,
                game=f'{self.game!r}',
                text=f"'{self.text.splitlines()[0][:20]}...'" if self.text else 'None',
                image=f"<{len(self.image)} bytes>" if self.image else 'None',
            )
        else:
            game = self.game
            return f"{self.__class__.__qualname__}({game=}, text=None, image=None, present=False)"

class GameDefinition:
    @classmethod
    def from_config(cls, cfg):
        pass

### Parsing games
class GameParseError(Exception):
    pass

def parse_lines(linelist):
    blank_line = lambda line: line[0:1] in {'\n', chr(0xFE0F), ''}
    res = dict(caption=[], result_rows=[], rows=0, cols=0,)
    for line in linelist:
        if line.startswith("http"): # link lines, if they've escaped the filter earlier
            continue
        elif re.search('[A-Za-z0-9]', line): # result lines
            res['caption'].append(line + ('\n' if not line.endswith('\n') else ''))
        elif blank_line(line) and res['rows'] == 0: # blank lines
            continue
        elif blank_line(line):
            res['result_rows'].append('')
            res['rows'] += 1
        else:
            line = line.rstrip()
            if res['rows'] == 0:
                res['cols'] = sum(1 for i in line if i in CHAR_TO_FILE.keys())
            res['rows'] += 1
            res['result_rows'].append(line)
    while 0 < len(res['result_rows']) and res['result_rows'][-1] == '':
        res['result_rows'].pop()
    res['caption'] = ''.join(res['caption']).rstrip()
    res['success'] = not re.search('X/[0-9]|-/[0-9]|X&[0-9]/[0-9]', res['caption'])
    return res

MISSING_GAME = object()

@dataclass
class ParsedGame:
    source: typing.Any
    caption: str
    result_rows: list[str]
    rows: int
    cols: int
    success: bool
    image_data: None | bytes
    game_name: str | type(MISSING_GAME)

    reparse_registry = dict()

    def __repr__(self):
        return (
            '{class_}(source={source!r}, game={game!r}, rows={rows!r}, cols={cols!r}, '
            'caption={caption!r}, result_rows={result_rows!r}, image_data={image_data}, '
            'success={success!r})'
        ).format(
            class_=self.__class__.__qualname__,
            game=self.game_name,
            source=self.source,
            caption=self.caption, rows=self.rows, cols=self.cols,
            result_rows=self.result_rows,
            success=self.success,
            image_data=(f"<{len(self.image_data)} bytes>"
                        if self.image_data and len(self.image_data) > 100
                        else repr(self.image_data)))

    def __str__(self):
        short_caption = 'None' if self.caption is None else self.caption.splitlines()[0]
        return (
            '<{class_} {game} {rows}x{cols} caption={caption} {image_data} {success}>'
        ).format(
            class_=self.__class__.__qualname__,
            game=self.game_name,
            caption=repr((short_caption + '...') if '\n' in self.caption else short_caption),
            rows=self.rows, cols=self.cols,
            success='SUCCESS' if self.success else 'FAIL',
            image_data=(f'image_data:{len(self.image_data)} bytes'
                        if isinstance(self.image_data, bytes)
                        else f'image_data={self.image_data!r}'))

    @classmethod
    def reparser_for(cls, game):
        def wrap(fn):
            cls.reparse_registry[game] = fn
            return fn
        return wrap

    @classmethod
    def missing_game(cls, game_name):
        return cls(
            game_name=MISSING_GAME,
            source=None,
            caption=game_name,
            result_rows=[], rows=0, cols=0, success=False,
            image_data=None)

# These continue to be super special boys so they have to be treated specially:
@dataclass
class Redactle(ParsedGame):
    guesses: int
    accuracy: float
    def __post_init__(self):
        self.game_name = 'redactle'
    def __str__(self):
        return '<{class_} {guesses}g {accuracy}% caption={caption} {success}>'.format(
            class_=self.__class__.__qualname__,
            caption=repr(self.caption),
            guesses=self.guesses, accuracy=self.accuracy,
            success='SUCCESS' if self.success else 'FAIL')

class GameParser:
    def _find_reparse(self, raw_parse):
        reparse_target = ParsedGame.reparse_registry.get(raw_parse.game_name, lambda x: x)
        logger.info(f'Using {reparse_target} for {raw_parse.source}')
        return reparse_target(raw_parse)

    def load(self, linelist, source=None, image_data=None):
        res = parse_lines(linelist)
        maybe_image_file = (re.sub('txt$', 'png', source)
                            if isinstance(source, str)
                            else None)
        if isinstance(image_data, bytes):
            res['image_data'] = image_data
        elif maybe_image_file is not None and os.path.isfile(maybe_image_file):
            res['image_data'] = maybe_image_file
        else:
            res['image_data'] = None
        return self._find_reparse(
            ParsedGame(**res, source=source, game_name=source.short_name))

    def load_string(self, string, cfg):
        # String shall be identified first before parsing
        for game in cfg.collection.collection:
            if game.matches(string):
                return self.load(string.splitlines(), game)

    def load_record(self, db_result):
        if game_text := db_result.text:
            return self._find_reparse(
                ParsedGame(**parse_lines(game_text.splitlines()),
                           image_data=db_result.image,
                           game_name=db_result.game,
                           source=db_result))
        else:
            logger.warn(f'No data for {db_result}; using missing_game')
            return ParsedGame.missing_game(db_result.game)

@ParsedGame.reparser_for('celtix')
def reparse_celtix(game: ParsedGame) -> ParsedGame:
    if dat := re.search('Celtix ([0-9]+) using ([0-9]+) wall', game.caption):
        cols = 8
        score = int(dat.group(2))
        puzzle_number = dat.group(1)
        cells = math.ceil(score / cols) * cols
        game.caption = f'Celtix {puzzle_number}'
        game.rows = cells // cols
        game.cols = cols
        game.result_rows = textwrap.wrap(
            (chr(0x1F7E5) * score).ljust(cells, chr(0x2B1C)),
            cols)
        game.success = True
        return game
    else:
        raise GameParseError

@ParsedGame.reparser_for('connections')
def reparse_connections(game: ParsedGame) -> ParsedGame:
    if dat := re.search('Puzzle #([0-9]+)', game.caption):
        game.caption = f'Connections {dat.group(1)}'
        last_row = game.result_rows[-1]
        game.success = last_row == last_row[0] * len(last_row)
        return game
    else:
        raise GameParseError

@ParsedGame.reparser_for('kotoba')
def reparse_kotoba(game: ParsedGame) -> ParsedGame:
    if dat := re.search('([0-9]+) (1?[0-9X])+/12(\\?)?', game.caption):
        game.caption = f'言葉で遊ぼう\n{dat.group(1)} {dat.group(2)}/12{dat.group(3)}'
        return game
    else:
        raise GameParseError

@ParsedGame.reparser_for('hexcodle')
def reparse_hexcodle(game: ParsedGame) -> ParsedGame:
    if dat := re.search(
            '^I got Hexcodle #([0-9]+) in ([0-9])! Score: ([0-9]+)%', game.caption):
        game.caption = f'Hexcodle {dat.group(1)} {dat.group(2)}/5 @ {dat.group(3)}%'
        game.success = True
    elif dat := re.search(
            '^I didn\'t get Hexcodle #([0-9]+) :\\( Score: ([0-9]+)%', game.caption):
        game.caption = f'Hexcodle {dat.group(1)} X/5 @ {dat.group(3)}%'
        game.success = False
    else:
        raise GameParseError
    return game

@ParsedGame.reparser_for('diffle')
def reparse_diffle(game: ParsedGame) -> ParsedGame:
    if dat := re.search('([0-9]+) words / ([0-9]+) letters', game.caption):
        game.caption = f'Diffle {dat.group(1)}/{dat.group(2)}'
        return game
    else:
        raise GameParseError

@ParsedGame.reparser_for('redactle')
def reparse_redactle(game: ParsedGame) -> Redactle:
    if dat := re.search(
            r'[#Q]([0-9]+) in ([0-9]+) guess(?:es)? with an accuracy of ([0-9]+\.[0-9]+)%',
            game.caption):
        game.caption = f'Redactle {dat.group(1)}'
        return Redactle(**game.__dict__,
                        guesses=int(dat.group(2)),
                        accuracy=float(dat.group(3)))
    else:
        raise GameParseError
