import logging
import os
import sys
from datetime import datetime, UTC
import yaml
import toml
from types import SimpleNamespace
import pytz
import subprocess
import argparse
import platformdirs
from importlib.metadata import version

from .collect import GameCollection, CollectionStatus
from .game.detect import GameDefinition
from . import db
from . import collect_tk
from . import mkimg
from . import archiver
from . import desktop
from . import res
from . import timer

logger = logging.getLogger(__name__)
version = version("autowordle")
here_timezone = datetime.now(UTC).astimezone().tzinfo

def load_definitions(*, more_definitions_file=None, selected_games=None):
    return [GameDefinition(dict(short_name=k) | v)
            for (k, v)
            in (res.definitions()
                | (toml.load(more_definitions_file) if more_definitions_file else dict())
                ).items()
            if (k in selected_games if selected_games is not None else True)]

def make_outimg_config(dat):
    return SimpleNamespace(
        width=dat['width'],
        game_separation=dat['game_separation'],
        title_size=dat['title']['font_size'],
        subtitle_size=dat['title']['subtitle_font_size'],
        font=dat['title']['font'])

def make_outimg_font(dat):
    return SimpleNamespace(family=dat['content_font'], size=dat['content_font_size'],)

def make_timeline_spec(dat):
    return SimpleNamespace(
        left_edge=dat['left_edge'],
        border_width=dat['border_width'],
        height_per_bucket=dat['height_per_bucket'],
        width_per_second=dat['width_per_second'],
        font=dat['font'],
        font_size=dat['font_size'],
        colour=dat['colour'])

class Config:
    program_name = 'Autowordle'
    default_config_filename = platformdirs.user_config_path(
        'autowordle', ensure_exists=True) / 'games.yaml'
    home_dir = platformdirs.user_data_dir('autowordle', ensure_exists=True)
    def __repr__(self):
        return '<{class_} {file_loc} {date:%Y-%m-%d}>'.format(
            class_=self.__class__.__qualname__,
            file_loc=self.location,
            date=self.date)
    def __init__(self, args):
        self.location = args.config
        with open(self.location) as f:
            self.dat = yaml.load(f, yaml.SafeLoader)
        self.do_cleanup = args.cleanup
        self.do_collect = args.collect
        self.check_already_collected = args.check_collected
        self.install_desktop_file = args.install_desktop_file
        self.show_version = args.version
        self.timezone = pytz.timezone(self.dat['timezone'])
        self.date = args.date
        self.db = db.Db(self)
        self._outfile = os.path.expanduser(self.dat['output']['filename'])
        self.yaml_archive = self.dat['archives']['yaml']
        self.celtix_archive = self.dat['archives'].get('celtix')
        self.outimg_config = make_outimg_config(self.dat['output'])
        self.outimg_font = make_outimg_font(self.dat['output'])
        self.timeline = make_timeline_spec(self.dat['output']['timeline'])
        self.parsed_games = load_definitions(selected_games=self.dat['games'])
        self.collection = GameCollection(self.parsed_games, self.db, self.date)

    @classmethod
    def from_cmdline(cls):
        parser = argparse.ArgumentParser(
            description='Store and construct summary images for Wordle clones')
        for opt, desc in [('--cleanup', ('Clean up after image construction'
                                         ' (Overrideable in GUI)')),
                          ('--check-collected',
                           ("Exit if today's game is already collected"
                            " and collection is not in progress")),
                          ('--collect', 'Collect games')]:
            parser.add_argument(
                opt,
                action=argparse.BooleanOptionalAction,
                help=desc,
                default=True)
        parser.add_argument(
            '--install-desktop-file', help='Install a .desktop file, then exit',
            action='store_true')
        parser.add_argument(
            '--config',
            metavar='FILENAME',
            help='Configuration file location',
            default=cls.default_config_filename)
        parser.add_argument('-v', '--version',
                            help='Show version and exit', action='store_true')
        args = parser.parse_args()
        args.date = datetime.now(tz=here_timezone)
        return cls(args)

    @classmethod
    def from_args(cls, config_file=None, *,
                  collect=True, check_collected=True, cleanup=True,
                  install_desktop_file=False,
                  date=None):
        return cls(SimpleNamespace(
            config=config_file or cls.default_config_filename,
            cleanup=cleanup,
            collect=collect,
            check_collected=check_collected,
            install_desktop_file=install_desktop_file,
            date=date if date is not None else datetime.now(tz=here_timezone),
            version=False))

    def autowordle_outfile(self):
        return self.date.strftime(os.path.expanduser(self._outfile))

    def yaml_archive_file(self):
        return self.date.strftime(os.path.expanduser(self.yaml_archive))

    def window_titles(self):
        return {x.window_title for x in self.parsed_games}

    def mkimg(self):
        return mkimg.Mkimg(self)

    def timer(self):
        return timer.Query(self)

    def workers(self):
        return [
            (mkimg.MkimgWorker(self), collect_tk.ClipwaitThread.finish_event_name),
            (archiver.ArchiverWorker(self), mkimg.MkimgWorker.event_name)]

def check_already_collected(cfg):
    if os.path.isfile(cfg.autowordle_outfile()) and cfg.check_already_collected:
        status = subprocess.run([
            res.exe.yad,
            "--button=Copy today's image!gtk-ok",
            '--button=Close!gtk-cancel',
            '--image=dialog-warning',
            '--window-icon=dialog-warning',
            '--text', f"Today ({cfg.date:%Y-%m-%d})'s games are already collected.",
            '--title', cfg.program_name
        ])
        if status.returncode == 0:
            mkimg.send_result_to_clipboard(cfg)
        raise SystemExit(1)

def show_version(cfg):
    if cfg.show_version:
        print(f'{cfg.program_name} v{version}')
        raise SystemExit(0)

def install_desktop_file(cfg):
    if cfg.install_desktop_file:
        desktop.install_desktop_file()
        raise SystemExit(0)

def run_collect_gui(cfg):
    gui = collect_tk.GUI(cfg)
    cfg.do_cleanup = False # Don't clean up by default in GUI
    for worker, trigger in cfg.workers():
        gui.add_worker(worker, trigger)
    match gui.exec():
        case CollectionStatus.COMPLETE:
            pass
        case CollectionStatus.COMPLETE_FOR_NOW:
            logger.info('Collection complete for now')
        case CollectionStatus.INCOMPLETE:
            logger.info('Collection aborted')
            raise SystemExit(1)

def run_workers(cfg):
    for worker, _ in cfg.workers():
        worker.exec()

def top():
    try:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
        cfg = Config.from_cmdline()
        os.chdir(cfg.home_dir)
        show_version(cfg)
        install_desktop_file(cfg)
        check_already_collected(cfg)
        if cfg.do_collect: run_collect_gui(cfg)
        else: run_workers(cfg)
    except SystemExit as e:
        return e.code
    else:
        return 0
