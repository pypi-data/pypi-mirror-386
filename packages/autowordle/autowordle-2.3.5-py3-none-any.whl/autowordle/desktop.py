import configparser
import tempfile
import subprocess
import platformdirs
import logging
import shutil

from . import res

logger = logging.getLogger(__name__)

def install_desktop_file():
    desktop_file = configparser.RawConfigParser()
    desktop_file.optionxform = lambda option: option
    desktop_file['Desktop Entry'] = {
        'Type': 'Application',
        'Exec': 'autowordle',
        'Name': 'Autowordle',
        'GenericName': 'Wordle clone collector',
        'Categories': 'Game',
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = tmpdir/'autowordle.desktop'
        with open(filename, 'w') as f:
            desktop_file.write(f)
        subprocess.run([
            res.exe.desktop_file_install,
            '--dir=' + platformdirs.user_data_dir('applications'),
            filename
        ])

def install_config_file():
    target_file = platformdirs.user_config_path('autowordle', ensure_exists=True) / 'games.yaml'
    if (not target_file.is_file()) or target_file.stat().st_size == 0:
        shutil.copyfile(res.file_res('sample_config.yaml'), target_file)
    else:
        logger.warning(f'{target_file} already exists, not touching it.')

def touch_extra_games_file():
    (platformdirs.user_config_path('autowordle', ensure_exists=True) / "games.toml").touch()

def first_time_actions():
    install_desktop_file()
    install_config_file()
    touch_extra_games_file()

if __name__ == "__main__":
    first_time_actions()
