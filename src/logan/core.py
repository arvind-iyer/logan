from .logevent import LogEvent
from .file import FileIter


class Manager(object):
    def __init__(self):
        self._events = []
        pass

    def register_event(self, event: LogEvent):
        if event in self._events:
            return
        self._events.append(event)

    def remove_event(self, event: LogEvent):
        try:
            self._events.remove(event)
        except AttributeError:
            # event is not known
            pass

    def listen(self, filepath: str, follow: bool = True):
        logfile = FileIter(filepath, follow)
        try:
            for line in logfile:
                in_progress = False
                for e in self._events:
                    if not e.is_complete():
                        e.process(line)
                    if not e.is_complete():
                        in_progress = True
                if not in_progress:
                    return
        except KeyboardInterrupt:
            return
