from sh import tail
from functools import partial
import re
import time


def follow_log(filename, events):
    try:
        # lazy generator that will yield a line of text when available
        for line in tail("-f", filename, _iter=True):
            for e in events:
                print("Reading: " + line)
                e.process(line)
                if e.success():
                    print("success: ", repr(e))
                    return
                elif e.failed():
                    print("failed: ", repr(e))
                    return

    except KeyboardInterrupt:
        pass


class LogEvent(object):
    SUCCESS = 2
    STARTED = 1
    WAITING = 0
    FAILED = -1

    def __init__(self, start_regex, end_regex=None, timeout=5, autoreset=False):
        self.sr = start_regex
        self.er = end_regex
        self.timeout = timeout
        self.loglines = []
        self._state = self.WAITING
        self._must_reset = autoreset

    def _reinit(self):
        self._state = self.WAITING
        self.loglines = []
        self._matches = None

    def process(self, line):
        if self._state == self.WAITING:
            matches = re.search(self.sr, line)
            if matches:
                self._matches = matches.groups()
                self._starttime = time.time()
                self._state = self.STARTED
                self.loglines.append(line)
        elif self._state == self.STARTED:
            self.loglines.append(line)
            if time.time() - self._starttime > self.timeout:
                print("Timed out")
                self._state = self.FAILED
                return
            if self.er is None or re.search(self.er, line):
                # Found
                self._state = self.SUCCESS
                if self._must_reset:
                    self._reinit()

    def success(self):
        return self._state == self.SUCCESS

    def failed(self):
        return self._state == self.FAILED

    def __repr__(self):
        return "LogEvent instance: ({}) -> ({})\nLOGS:\n{}".format(
            self.sr, self.er, "".join(self.loglines)
        )

    def __str__(self):
        return "LogEvent instance: ({}) -> ({})".format(self.sr, self.er)
