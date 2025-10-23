import re
import os
import logging
from dataclasses import dataclass, field
import typing

from ..res import CHAR_TO_FILE

logger = logging.getLogger(__name__)

### Parsing games
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
    extra_results: typing.Any = field(init=False, default=None)

    def __repr__(self):
        return (
            '{class_}(game={game!r}, rows={rows!r}, cols={cols!r}, '
            'caption={caption!r}, result_rows={result_rows!r}, image_data={image_data}, '
            'extra_results={extra_results!r}, success={success!r})'
        ).format(
            class_=self.__class__.__qualname__,
            game=self.game_name,
            caption=self.caption, rows=self.rows, cols=self.cols,
            result_rows=self.result_rows,
            success=self.success,
            image_data=(f"<{len(self.image_data)} bytes>"
                        if self.image_data and len(self.image_data) > 100
                        else repr(self.image_data)),
            extra_results=self.extra_results,)

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
    def missing_game(cls, game_name):
        return cls(
            game_name=MISSING_GAME,
            source=None,
            caption=game_name,
            result_rows=[], rows=0, cols=0, success=False,
            image_data=None)

def _id(x): return x # Used for defining reparse functions that don't do anything

class GameParser:
    def __init__(self, game_definitions):
        self.reparse_registry = dict()
        for i in game_definitions:
            if i.reparse_actions != []:
                self.reparse_registry[i.code] = self._make_reparse_function(i)

    def _make_reparse_function(self, game_definition):
        def reparse_function(game_to_reparse: ParsedGame) -> ParsedGame:
            for reparser in game_definition.reparse_actions:
                reparser.op(game_to_reparse)
            return game_to_reparse
        return reparse_function

    def _find_reparse(self, raw_parse):
        reparse_target = self.reparse_registry.get(raw_parse.game_name, _id)
        logger.info(f'Using {reparse_target} for {raw_parse.source}')
        return reparse_target(raw_parse)

    def load(self, linelist, source, image_data=None):
        res = parse_lines(linelist) | {"source": source, "game_name": source.short_name}
        maybe_image_file = (re.sub('txt$', 'png', source)
                            if isinstance(source, str)
                            else None)
        if isinstance(image_data, bytes):
            res['image_data'] = image_data
        elif maybe_image_file is not None and os.path.isfile(maybe_image_file):
            res['image_data'] = maybe_image_file
        else:
            res['image_data'] = None
        return self._find_reparse(ParsedGame(**res))

    def load_string(self, string, cfg):
        # String shall be identified first before parsing
        for game in cfg.collection.collection:
            if game.matches(string):
                return self.load(string.splitlines(), game)

    def load_record(self, db_result):
        if db_result.image is not None and db_result.image.startswith(b'HASH:\n'):
            logger.warn('Image in game record has been replaced with hash.')
        if game_text := db_result.text:
            return self._find_reparse(
                ParsedGame(**parse_lines(game_text.splitlines()),
                           image_data=db_result.image,
                           game_name=db_result.game,
                           source=db_result))
        else:
            logger.warn(f'No data for {db_result}; using missing_game')
            return ParsedGame.missing_game(db_result.game)
