from wand.image import Image
from wand.color import Color
from wand.drawing import Drawing
from wand.font import Font
from datetime import datetime, timedelta
import math
from types import SimpleNamespace
import logging
import tempfile
import subprocess
import hashlib

from . import timer
from .collect_tk import Worker
from .res import CHAR_TO_FILE, colours, colr_res, file_res
from . import game as gamelib

logger = logging.getLogger(__name__)

class GameImage:
    handlers = dict()

    def __init__(self, font=SimpleNamespace(family='Noto-Sans-CJK-TC', size=18)):
        self.font = font

    @classmethod
    def handler(cls, game):
        def wrap(fn):
            cls.handlers[game] = fn
            return fn
        return wrap

    def populate_result_grid(self, game, result_grid):
        return self.handlers.get(game.game_name, self._populate_result_grid)(self.font, game, result_grid)

    def _populate_result_grid(self, _, game, result_grid):
        for row in game.result_rows:
            if row == '':
                for i in range(game.cols):
                    with Image(width=20, height=3, filename=colr_res(colours.white)) as item:
                        result_grid.image_add(item)
            else:
                for char in row:
                    if resource := CHAR_TO_FILE.get(char):
                        with Image(width=20, height=20, filename=resource) as item:
                            result_grid.image_add(item)
        result_grid.montage(tile=f'{game.cols}x{game.rows}', thumbnail='+2+2')
        return result_grid

    def make_image(self, game, game_image=None):
        if game_image is None:
            game_image = Image()
        with Image() as result_grid:
            game_image.font = Font(
                self.font.family,
                self.font.size,
                colours.black if game.success else colours.red
            )
            game_image.read(filename=f"label:{game.caption}")
            game_image.image_add(self.populate_result_grid(game, result_grid))
            game_image.smush(stacked=True, offset=5)
            logger.info(f'Constructed image for {game}')
            return game_image

@GameImage.handler(gamelib.MISSING_GAME)
def missing_image_result_grid(_, _game, result_grid):
    result_grid.read(filename=file_res('missing-image.png'))
    return result_grid

@GameImage.handler('diffle')
def diffle_result_grid(_, game, result_grid):
    if isinstance(game.image_data, str):
        result_grid.read(filename=game.image_data)
    elif isinstance(game.image_data, bytes):
        result_grid.read(blob=game.image_data)
    result_grid.chop(width=0, height=70, gravity='north')
    return result_grid

@GameImage.handler('redactle')
def redactle_result_grid(font, game, result_grid):
    result_grid.read(filename=file_res('redactle-base.png'))
    guess_width = math.log(game.extra_results.guesses, 10) * 100
    accuracy_width = game.extra_results.accuracy / 100 * 300
    with Drawing() as ctx:
        ctx.fill_color = Color(colours.red)
        ctx.rectangle(left=80, top=20, width=guess_width, height=10)
        ctx.fill_color = Color(colours.green)
        ctx.rectangle(left=80, top=60, width=accuracy_width, height=10)
        ctx.font = font.family
        ctx.font_size = font.size
        ctx.fill_color = Color('black')
        ctx.text(0, 18, str(game.extra_results.guesses))
        ctx.text(0, 55, str(game.extra_results.accuracy) + '%')
        ctx(result_grid)
    return result_grid

class Timeline:
    minutes_per_row = 30
    def __init__(self, config):
        self.config = config
        self.outcfg = config.outimg_config
        self.timeline_spec = config.timeline

    def _halfhour_bucket(self, timestamp):
        return timestamp.replace(minute=((timestamp.minute // self.minutes_per_row)
                                         * self.minutes_per_row),
                                 second=0,
                                 microsecond=0)

    def _read_timestamp(self, timestring):
        return datetime.fromisoformat(timestring).astimezone(self.config.timezone)

    def _in_bucket(self, timestamp, buckets):
        halfhour = self._halfhour_bucket(timestamp)
        for i, ts in enumerate(buckets):
            if halfhour == ts:
                return i

    def _timeline_rectangle(self, event, buckets, width_per_second, height_per_bucket, left_edge):
        event_timestamp = self._read_timestamp(event['timestamp'])
        x = (left_edge
             + (event_timestamp.minute % self.minutes_per_row * 60 + event_timestamp.second)
             * width_per_second)
        y = self._in_bucket(event_timestamp, buckets) * height_per_bucket
        w = event['duration'] * width_per_second
        h = height_per_bucket
        return (x, y, w, h)

    def make_image(self, events):
        width_per_second = self.timeline_spec.width_per_second
        height_per_bucket = self.timeline_spec.height_per_bucket
        left_edge = self.timeline_spec.left_edge
        border_width = self.timeline_spec.border_width
        buckets = list(sorted({self._halfhour_bucket(self._read_timestamp(i['timestamp']))
                               for i in events}))

        # If there are no events, then don't bother with a timeline:
        if len(events) == 0:
            return Image(width=self.outcfg.width, height=border_width,
                         pseudo=colr_res(colours.border))
        # If the last entry extends past the half-hour mark, then add a new bucket:
        last_entry = events[-1]
        last_entry_ts = self._read_timestamp(last_entry['timestamp'])
        if (self._halfhour_bucket(last_entry_ts) !=
            self._halfhour_bucket(last_entry_ts
                                  + timedelta(seconds=last_entry['duration']))):
            buckets.append(buckets[-1] + timedelta(minutes=self.minutes_per_row))

        img = Image(width=int(width_per_second * self.minutes_per_row * 60) + left_edge,
                    height=len(buckets) * height_per_bucket,
                    pseudo=colr_res(colours.border))
        img.background_color = colours.border
        for i, b in enumerate(buckets): # Half hour labels
            img.caption(b.strftime('%H:%M'),
                        left=0, top=i * height_per_bucket,
                        width=left_edge, height=height_per_bucket,
                        gravity='center',
                        font=Font(self.timeline_spec.font,
                                  self.timeline_spec.font_size, colours.white))

        with Drawing() as ctx:
            # Background
            ctx.fill_color = Color(colours.white)
            ctx.rectangle(left=left_edge, top=0,
                          width=width_per_second * self.minutes_per_row * 60,
                          height=len(buckets) * height_per_bucket)
            for i in range(1, self.minutes_per_row): # 1 minute marks
                ctx.fill_color = Color(colours.border if i % 5 == 0
                                       else self.timeline_spec.colour)
                ctx.line((i * 60 * width_per_second + left_edge, 0),
                         (i * 60 * width_per_second + left_edge, height_per_bucket * len(buckets)))
            for i in events:
                ctx.fill_color = Color('#' + hashlib.md5(i['data']['title'].encode('utf-8')).hexdigest()[0:6])
                x, y, w, h = self._timeline_rectangle(i, buckets, width_per_second, height_per_bucket, left_edge)
                ctx.rectangle(left=x, top=y, width=w, height=h)
                if x + w > img.width: # Wrap around if event crosses the half-hour mark
                    ctx.rectangle(left=left_edge, top=y + height_per_bucket,
                                  right=x + w - width_per_second * self.minutes_per_row * 60,
                                  height=h)
            ctx.draw(img)
        img.extent(width=self.outcfg.width, height=img.height + 2 * border_width,
                   gravity='center')
        return img

class Header:
    def __init__(self, config):
        self.outcfg = config.outimg_config
        self.date = config.date

    def make_image(self, time_taken):
        img = Image()
        with Image(pseudo=colr_res(colours.theme2), height=45, width=self.outcfg.width) as title:
            title.font = Font(self.outcfg.font, self.outcfg.title_size, colours.theme1)
            title.label("Wordle-Like Statistics", gravity='center')
            img.image_add(title)
        with Image(pseudo=colr_res(colours.theme2), height=40, width=self.outcfg.width) as subtitle:
            subtitle.font = Font(self.outcfg.font, self.outcfg.subtitle_size, colours.theme1)
            subtitle.label(
                "{date:%Y-%m-%d}{time_taken}".format(
                    date=self.date,
                    time_taken=f' - {time_taken} minutes' if time_taken else '',
                ),
                gravity='center',
            )
            img.image_add(subtitle)
        return img

class Mkimg:
    def __init__(self, config):
        self.config = config
        self.layout = config.dat['layouts'][0]
        self.outcfg = config.outimg_config
        self.activitywatch = timer.Query(config)
        self.header = Header(config)
        self.timeline = Timeline(config)
        self.game_image_maker = GameImage(config.outimg_font)
        self.game_parser = gamelib.GameParser(config.parsed_games)
        self.games = {game.short_name: self.game_parser.load_record(game.result)
                      for game in config.collection.collection}

    def summary_subsequence(self, seq, layout, vertical, recur=0):
        if isinstance(layout, str):
            with Image() as game_image:
                game = self.games.get(layout)
                if game is None:
                    logger.warn(f'Game {layout} not found in collected games; '
                                'using fallback missing game picture')
                    game = gamelib.ParsedGame.missing_game(layout)
                seq.image_add(
                    self.game_image_maker.make_image(game, game_image))
        elif isinstance(layout, list):
            with Image() as subseq:
                for i in layout:
                    self.summary_subsequence(subseq, i, not vertical, recur + 1)
                if recur == 0: # Centre the highest-level rows
                    for i in range(subseq.iterator_length()):
                        subseq.iterator_set(i)
                        logger.info(f'Row {i} is {subseq.width} x {subseq.height}')
                        if subseq.width > self.outcfg.width:
                            logger.warning(
                                f'Row {i} is {subseq.width} wide,'
                                'which is more than the specified width '
                                f'of the output image ({self.outcfg.width}). '
                                'Data may fall out of the edge of the image.')
                        subseq.extent(width=self.outcfg.width, gravity='north')
                subseq.smush(stacked=vertical, offset=self.outcfg.game_separation)
                seq.image_add(subseq)
        else:
            raise ValueError('Image layout can only contain games (strings) '
                             'inside possibly nested lists. '
                             f'Got {layout}')

    def make_image(self):
        img = Image()
        with (self.header.make_image(self.activitywatch.time_taken()) as header,
              self.timeline.make_image(self.activitywatch.matching_events()) as timeline):
            img.gravity = 'north'
            img.image_add(header)
            img.image_add(timeline)
            self.summary_subsequence(img, self.layout, True)
            img.smush(stacked=True,)
            return img

    def summary_image(self):
        outfile = self.config.autowordle_outfile()
        with (self.make_image() as final,
              tempfile.NamedTemporaryFile(prefix=self.config.program_name.lower()) as f):
            final.format = 'png'
            final.save(f)
            subprocess.run(['pngcrush', f.name, outfile])
        with open(outfile, 'rb') as result_file:
            self.config.db.record_generated_image(
                self.config.date.strftime('%Y-%m-%d'),
                hashlib.file_digest(result_file, "sha256").digest())
        logger.info(f'Image sent to {outfile}.')

def send_result_to_clipboard(cfg):
    subprocess.run(
        ['xclip', '-sel', 'c', '-target', 'text/uri-list'],
        input=f'file://{cfg.autowordle_outfile()}',
        text=True)

class MkimgWorker(Worker):
    event_name = "<<MkimgDone>>"
    def exec(self):
        Mkimg(self.config).summary_image()
        send_result_to_clipboard(self.config)
    def hook(self):
        self.gui.new_status(f'Image constructed and sent to {self.config.autowordle_outfile()}')
