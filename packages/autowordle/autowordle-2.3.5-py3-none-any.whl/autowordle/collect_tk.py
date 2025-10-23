from tkinter import PhotoImage, NORMAL, END, DISABLED, Text, HORIZONTAL, ttk
from ttkthemes import ThemedTk
from importlib.metadata import version
import threading
import subprocess
import logging

from .collect import GameStatus, CollectionStatus, clipboard
from .res import file_res, exe

logger = logging.getLogger(__name__)

class TetsudoruCommands:
    def __init__(self, gui=None):
        self.gui = gui

    strings = [
        "tetsudoru -1 | grep -v '[きぎただあさざかが]'",
        "tetsudoru -1 | grep -v '[きぎただあさざかがつっづしじんまちぢ]'",
        "tetsudoru -1 | grep -v '[きぎただあさざかがつっづしじんまちぢいよひびぴらの]'",
    ]
    def to_clipboard(self, idx):
        subprocess.run([exe.xclip, '-sel', 'c'], input=self.strings[idx - 1], text=True)
        if self.gui is not None:
            self.gui.new_status(f"Sent search string for Tetsudoru ({idx} guesses)")

class ClipwaitThread:
    event_name = "<<NewClipboard>>"
    finish_event_name = "<<CollectionComplete>>"
    def __init__(self, gui, *, daemon=False):
        self.gui = gui
        self.col = gui.col
        self.daemon = daemon
        gui.bind_event(self.event_name, lambda e: self.hook())
    def _exec(self):
        subprocess.run([exe.clipnotify])
        self.gui.fire_event(self.event_name)
    def start(self):
        threading.Thread(target=self._exec, daemon=self.daemon).start()
        logger.debug('New clip wait thread spawned')
    def hook(self):
        dat = clipboard()
        # self.gui.update_clipboard(dat)
        if matchp := self.col.find_matching_game(dat):
            self.gui.update_games_view(matchp)
        match self.col.status():
            case CollectionStatus.INCOMPLETE:
                self.start()
            case CollectionStatus.COMPLETE_FOR_NOW:
                self.gui.new_status('Collection complete; no longer listening on clipboard.')
            case CollectionStatus.COMPLETE:
                self.gui.fire_event(self.finish_event_name)

class Worker:
    event_name = None
    def __init__(self, config):
        self.config = config
        self.gui = None
    def inject_gui(self, gui, kickoff_event):
        self.gui = gui
        gui.bind_event(kickoff_event, lambda e: self.start(), append=True)
        gui.bind_event(self.event_name, lambda e: self.hook())
    def exec(self):
        pass
    def _exec(self):
        self.exec()
        if self.gui is not None:
            self.gui.fire_event(self.event_name)
    def start(self):
        self.thread = threading.Thread(target=self._exec)
        self.thread.start()
    def hook(self):
        pass

# class App(slint.loader.app_window.AppWindow):
#     _icons = {
#         GameStatus.COLLECTED: '✓',
#         GameStatus.UNCOLLECTED: ' ',
#         GameStatus.UNELIGIBLE: '·',
#         GameStatus.PARTIALLY_COLLECTED: '–',
#         GameStatus.OPTIONAL: ' ',
#     }

#     def __init__(self, config):
#         self.workers = dict()
#         self.tetsudoru = TetsudoruCommands(self)

#         super().__init__()
#         self._games = [slint.ListModel(
#             [{"text": i["status"]}, {"text": i["game"]}, {"text": i["detail"]}]
#         ) for i in games]
#         self.games = slint.ListModel(self._games)

#     def new_status(self, text):
#         self.status = text

#     def update_games_view(self, game):
#         raise NotImplementedError("WIP")

#     def add_worker(self, worker, kickoff_event):
#         raise NotImplementedError("WIP")

#     def fire_event(self, event_name):
#         raise NotImplementedError("WIP")

#     def enable_quit_button(self, quit_button_function):
#         raise NotImplementedError("WIP")

#     def bind_key(self, key, function):
#         raise NotImplementedError("WIP")

#     def bind_event(self, key, function, append=False):
#         raise NotImplementedError("WIP")

#     @slint.callback
#     def quit(self):
#         self.hide()

#     @slint.callback
#     def try_something(self):
#         self._games[1].set_row_data(0, {"text": "✓"})
#         self._games[1].set_row_data(2, {"text": "It has been collected"})

#     @slint.callback
#     def tetsudoru_guesses(self, num_guesses):
#         num_guesses = int(num_guesses)
#         self.tetsudoru.to_clipboard(num_guesses)
#         self.new_status(
#             "Sent search string for Tetsudoru "
#             f"({num_guesses} guess{'es' if num_guesses != 1 else ''})")

class GUI:
    _icons_files = {
        GameStatus.COLLECTED: 'emblem-default-symbolic.png',
        GameStatus.UNCOLLECTED: 'emblem-error.png',
        GameStatus.UNELIGIBLE: 'emblem-readonly.png',
        GameStatus.PARTIALLY_COLLECTED: 'emblem-remove.png',
        GameStatus.OPTIONAL: 'emblem-question.png',
    }

    def __init__(self, config):
        self.col = config.collection
        self.root = ThemedTk(theme='breeze', className=config.program_name.lower())
        self.workers = list()
        self.date = config.date
        self.complete = False
        self.tetsudoru = TetsudoruCommands(self)
        self.root.title(f'{config.program_name}: {config.date:%Y-%m-%d}')
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._icons = {k: PhotoImage(file=file_res(v), format='png')
                       for (k, v) in self._icons_files.items()}
        self.clipwait_thread = ClipwaitThread(self, daemon=True)
        self.col.inject_gui(self)

    def _title(self):
        return "Version {}; collecting for {:%Y-%m-%d}".format(
            version("autowordle"), self.date)

    def add_worker(self, worker, kickoff_event):
        worker.inject_gui(self, kickoff_event)
        self.workers.append(worker)
        logger.info(f'Added worker {worker} on event {kickoff_event}')

    def update_clipboard(self, new_text):
        self.clipboard_display.config(state=NORMAL)
        self.clipboard_display.delete('1.0', END)
        if isinstance(new_text, str):
            self.clipboard_display.insert(END, new_text)
        else:
            self.clipboard_display.insert(END, '<Non-text data>')
        self.clipboard_display.config(state=DISABLED)

    def update_games_view(self, game):
        new_status = game.status()
        self.games_view.item(
            game.short_name,
            values=(game.name, game.status_str()),
            image=self._icons[new_status])
        if new_status == GameStatus.COLLECTED:
            self.progress_bar.step(1)

    def new_status(self, status_text):
        self.status.config(text=status_text)
        logger.info(status_text)

    def fire_event(self, event_name):
        self.root.event_generate(event_name)

    def enable_quit_button(self, quit_button_function):
        self.quit_button.config(state='enabled')

    def bind_key(self, key, function):
        self.root.bind(key, function)

    def bind_event(self, event_name, function, append=False):
        self.root.bind(event_name, function, add='+' if append else None)

    def _add_buttons(self, frm):
        buttons = ttk.Frame(frm, padding=10)
        buttons.grid(row=3, column=1, columnspan=2)
        buttons.grid()
        for i, _ in enumerate(self.tetsudoru.strings):
            plural = "es" if 0 < i else ""
            ttk.Button(
                buttons,
                text=f"Tetsudoru ({i + 1} guess{plural})",
                command=(lambda i: lambda: self.tetsudoru.to_clipboard(i + 1))(i)
            ).grid(column=i, row=1)
            quit_button = ttk.Button(buttons, text="Quit", command=self.root.destroy)
            quit_button .grid(column=0, row=2, columnspan=3, sticky='nesw')
            self.quit_button = ttk.Button(
                buttons,
                text="Clean up and finish",
                state=DISABLED)
            self.quit_button.grid(column=0, row=3, columnspan=3, sticky='nesw')
    def _add_clipboard_frame(self, frm):
        clipboard_frame = ttk.Frame(frm, borderwidth=1, width=400, padding=10)
        clipboard_frame.grid(column=0, row=0, rowspan=4, sticky='nesw')
        clipboard_frame.grid()
        ttk.Label(clipboard_frame, text="Clipboard", anchor="w",).grid(column=0, row=0)
        self.clipboard_display = Text(clipboard_frame, width=50, height=30)
        self.clipboard_display.config(state=DISABLED)
        self.clipboard_display.grid(column=0, row=1, sticky='nesw')
    def _add_progress_bar(self, frm):
        ttk.Label(frm, text='Collection progress', width=1).grid(row=2, column=1, sticky='ew')
        self.progress_bar = ttk.Progressbar(
            frm,
            maximum=sum(1 for i in self.col.collection if i.eligiblep())
        )
        self.progress_bar.grid(row=2, column=2, sticky='nesw')
        self.progress_bar.step(sum(1 for i in self.col.collection
                           if i.status() == GameStatus.COLLECTED))
    def _add_games_view(self, frm):
        self.games_view = ttk.Treeview(
            frm,
            padding=10,
            columns=('name', 'status'),
            height=len(self.col.collection))
        self.games_view.column('#0', width=50)
        self.games_view.heading('name', text='Name')
        self.games_view.column('name', width=150)
        self.games_view.heading('status', text='Status')
        self.games_view.column('status', width=300)
        self.games_view.grid(column=1, row=1, columnspan=2)
        for game in self.col.collection:
            self.games_view.insert(
                '', 'end', game.short_name,
                values=(game.name, game.status_str()),
                image=self._icons[game.status()])
    def _add_status_bar(self, frm):
        ttk.Separator(frm, orient=HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky='ew')
        self.status = ttk.Label(frm, text='')
        self.status.grid(row=2, column=0, sticky='ew')
    def _mark_complete(self, _event):
        self.complete = True

    def exec(self):
        top_frame = ttk.Frame(self.root)
        top_frame.grid()
        main_widget_frame = ttk.Frame(top_frame, padding=10)
        main_widget_frame.grid(row=0, column=0)
        main_widget_frame.grid()
        ttk.Label(main_widget_frame, text=self._title()).grid(row=0, column=1, columnspan=2)
        self._add_games_view(main_widget_frame)
        self._add_buttons(main_widget_frame)
        # self._add_clipboard_frame(main_widget_frame)
        self._add_progress_bar(main_widget_frame)
        self._add_status_bar(top_frame)

        self.root.bind('q', lambda _: self.root.destroy())
        self.root.bind(ClipwaitThread.finish_event_name, self._mark_complete, add='+')

        if self.col.status() == CollectionStatus.COMPLETE:
            self.root.event_generate(ClipwaitThread.finish_event_name)
        else:
            self.clipwait_thread.start()
            self.new_status('Listening on clipboard...')
        self.root.mainloop()
        return CollectionStatus.COMPLETE if self.complete else self.col.status()
