from . import prog
from . import mkimg
from . import collect
from . import collect_tk
from . import timer
from . import game
from . import ipc
from .prog import Config
from .prog import top as run

config = Config.from_args
version = prog.version

__all__ = ['prog', 'mkimg', 'collect', 'game', 'collect_tk', 'timer', 'ipc',
           'config', 'run', 'version']
