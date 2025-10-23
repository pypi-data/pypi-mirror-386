from .collect_tk import Worker
import subprocess

from . import res

def send_message_to_emacs():
    subprocess.run([
        res.qdbus, 'org.gnu.Emacs', '/org/gnu/Emacs/isoraqathedh',
        'org.gnu.Emacs.isoraqathedh.stopWordleClock'
    ])

class EmacsNotifyWorker(Worker):
    event_name = "<<DbusMessageSent>>"
    def exec(self):
        send_message_to_emacs()
