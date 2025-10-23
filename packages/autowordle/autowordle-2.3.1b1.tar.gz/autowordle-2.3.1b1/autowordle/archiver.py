import os
import logging
import re
import hashlib

from .collect_tk import Worker
from .res import Audio
from .db import GameRecord

logger = logging.getLogger(__name__)

yaml_fragment = """\
? ["{game}", "{date}"]
:
  dat: |
{text}
  timestamp: {timestamp}
"""

class Archiver:
    def __init__(self, config):
        self.config = config

    def game_object(self, date, record):
        return yaml_fragment.format(
            game=record.game,
            date=date,
            timestamp=record.timestamp.isoformat(),
            text='\n'.join(' ' * (4 if l != '' else 0) + l
                           for l in record.text.splitlines()).rstrip())

    def strings_for_date(self, datestring):
        return ''.join(self.game_object(datestring, i)
                       for i in self.config.db.load_date(datestring))

    def dump_to_file(self):
        outfile = self.config.yaml_archive_file()
        with open(outfile, 'a') as f:
            f.write(self.strings_for_date(self.config.date.strftime('%Y-%m-%d')))
        logger.info(f'Data sent to {outfile}.')

    def celtix_cleanup(self):
        if self.config.celtix_archive is None: return
        today = self.config.date.strftime('%Y-%m-%d')
        match self.config.db.load(today, 'celtix'):
            case GameRecord(game='celtix', image=bytes() as image) if image.startswith(b'HASH:\n'):
                logger.warning('Already moved the image out of the database, skipping.')
            case GameRecord(game='celtix', text=str() as text, image=bytes() as image) \
                 if ((puznum_match := re.search('#Celtix ([0-9]+)', text))
                     and not image.startswith(b'HASH:\n')):
                celtix_dest = os.path.expanduser(self.config.celtix_archive.format(
                    puznum=puznum_match.group(1),
                    date=self.config.date))
                with open(celtix_dest, 'wb') as f:
                    f.write(image)
                with open(celtix_dest, 'rb') as f:
                    filehash = hashlib.file_digest(f, 'sha256')
                    self.config.db.save(today, 'celtix', b'HASH:\n' + filehash.digest())
                logger.info(f'Moved Celtix result to {celtix_dest}; '
                            f'memory database replaced with hash {filehash.hexdigest()}')
            case GameRecord(game='celtix', text=str(), image=bytes()):
                logger.warning('Cannot detect puzzle number from found Celtix result, skipping')
            case GameRecord(text=None) | GameRecord(image=None):
                logger.info('No Celtix image is found, skipping')
            case otherwise:
                raise RuntimeError('Unexpected state when cleaning up Celtix: '
                                   f'got {otherwise} from loading from database')

class ArchiverWorker(Worker):
    event_name = "<<ArchiveComplete>>"
    def exec(self):
        if self.config.do_cleanup:
            cleanup = Archiver(self.config)
            cleanup.celtix_cleanup()
            cleanup.dump_to_file()
    def hook(self):
        Audio.COMPLETE.play()
        self.gui.root.bind('<space>', lambda _: self.archive_and_quit())
        self.gui.quit_button.config(state='enabled', command=self.archive_and_quit)
    def archive_and_quit(self):
        self.config.do_cleanup = True
        self.gui.new_status("Cleaning up...")
        self.exec()
        self.gui.root.destroy()
