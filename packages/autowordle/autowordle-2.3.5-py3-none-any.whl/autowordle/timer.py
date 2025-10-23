from datetime import timedelta
from importlib.util import find_spec as is_module_present
import logging

QUERY = """
events = query_bucket('aw-watcher-window_fiventsu');
not_afk = flood(query_bucket(find_bucket("aw-watcher-afk_fiventsu")));
not_afk = filter_keyvals(not_afk, "status", ["not-afk"]);
RETURN = filter_period_intersect(events, not_afk);
"""
_logger = logging.getLogger(__name__)

class Query:
    _disabled = object()
    def __repr__(self):
        return "<{class_name} {has_data} starting {date:%Y-%m-%d %H:%M:%S}>".format(
            class_name=type(self).__qualname__,
            has_data="NO DATA" if self.events is None else "loaded",
            date=self.date
        )
    def __init__(self, cfg):
        self.events = None
        self.timezone = cfg.timezone
        last_completed_time = cfg.db.latest_generated_image(cfg.date.astimezone().isoformat())
        self.date = max(cfg.date - timedelta(hours=18), last_completed_time)
        _logger.info(f'Timer is counting from {self.date:%d%H%MJ}')
        self.window_titles = cfg.window_titles()

    def _ensure_query_run(self):
        if not is_module_present('aw_client'):
            _logger.warning('ActivityWatch not installed but timer called anyway')
            self.events = self._disabled
        elif self.events is None:
            from aw_client import ActivityWatchClient
            cl = ActivityWatchClient("wordle-clone-query-" + __name__)
            self.events = cl.query(QUERY, [(self.date, self.date + timedelta(days=1))])[0]

    def time_taken(self):
        self._ensure_query_run()
        if self.events is self._disabled:
            return 0
        return int(round(sum(e["duration"] for e in self.matching_events()) / 60, 0))

    def matching_events(self):
        self._ensure_query_run()
        if self.events is self._disabled:
            return []
        return [event for event in self.events
                if any(event["data"]["title"].startswith(keys)
                       for keys in self.window_titles)]
