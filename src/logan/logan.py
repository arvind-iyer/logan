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

    def __init__(self, start_regex, end_regex, timeout=5, autoreset=False):
        self.sr = start_regex
        self.er = end_regex
        self.timeout = timeout
        self.loglines = []
        self._count = self.WAITING
        self._must_reset = autoreset

    def _reinit(self):
        self._count = self.WAITING
        self.loglines = []
        self._matches = None

    def process(self, line):
        if self._count == self.WAITING:
            matches = re.search(self.sr, line)
            if matches:
                self._matches = matches.groups()
                self._starttime = time.time()
                self._count = self.STARTED
                self.loglines.append(line)
        elif self._count == self.STARTED:
            self.loglines.append(line)
            if time.time() - self._starttime > self.timeout:
                print("Timed out")
                self._count = self.FAILED
                return
            matches = re.search(self.er, line)
            if matches:
                # Found
                self._count = self.SUCCESS
                if self._must_reset:
                    self._reinit()

    def success(self):
        return self._count == self.SUCCESS

    def failed(self):
        return self._count == self.FAILED

    def __repr__(self):
        return "LogEvent instance: ({}) -> ({})\nLOGS:\n{}".format(
            self.sr, self.er, "".join(self.loglines)
        )

    def __str__(self):
        return "LogEvent instance: ({}) -> ({})".format(self.sr, self.er)
