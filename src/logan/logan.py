import re
import time
from typing import List, Pattern, Optional, Callable
from sh import tail

__all__ = ["LogEvent", "attach_events"]


class LogEvent(object):
    SUCCESS = 2
    STARTED = 1
    WAITING = 0
    FAILED = -1
    _subber = re.compile("`(\d+)`")

    def __init__(
        self,
        start_regex: Pattern,
        end_regex: Optional[Pattern] = None,
        title: str = "",
        timeout: float = 5,
        autoreset: bool = False,
    ):
        """
        Defines a regular expression (or optionally 2) that will be
        searched in a log file.

        @params:
            start_regex: instance of re.Pattern
                can be created by calling re.compile() on a regular expression.
                If the current log line matches this, a timer is started and
                we attempt to match for the end_regex expression.
            end_regex: instance of re.Pattern. [Optional]
                After the start_regex is found, we will attempt to match with
                this pattern(if provided). If not provided, the status is
                immediately set to SUCCESS. If provided and this pattern is
                found within the timeout period, the event is a success, else
                fail.
            timeout: float [Default = 5 seconds]
                Timeout period in seconds
            autoreset: bool [Default = False]
                On completion of event, this will immediately reset the
                instance and begin looking for the start_regex again.
                Useful if the callbacks are set and are used to trigger
                external activity.
        """
        self.sr = start_regex
        self.er = end_regex
        self.timeout = timeout
        self.loglines: List[str] = []

        self._state = self.WAITING
        self._must_reset = autoreset
        self._starttime = time.time()
        if len(title) == 0:
            self.title = self.sr.pattern
        else:
            self.title = title

    def _reinit(self):
        self._state = self.WAITING
        self.loglines = []
        self._matches = None

    def process(self, line: str):
        if (time.time() - self._starttime) > self.timeout:
            self.reason = "Timed out"
            self.set_state(self.FAILED)
        if self._state == self.WAITING:
            # Look for first pattern
            matches = self.sr.search(line)
            if matches:
                # TODO: Use _matches to find previously found
                # strings in end_regex
                self._matches = matches.groups()
                self.set_state(self.STARTED)
                self.loglines.append(line)
                if self.er is None:
                    self.set_state(self.SUCCESS)
        elif self._state == self.STARTED:
            # Look for second pattern
            self.loglines.append(line)
            if self.er.search(line):
                # Found
                self.set_state(self.SUCCESS)

    @property
    def on_success(self) -> Callable[..., None]:
        if hasattr(self, "_on_success"):
            return self._on_success
        else:
            return lambda x: None

    @on_success.setter
    def on_success(self, callback: Callable[..., None]):
        self._on_success = callback

    @property
    def on_failed(self) -> Callable[..., None]:
        if hasattr(self, "_on_failed"):
            return self._on_failed
        else:
            return lambda x: None

    @on_failed.setter
    def on_failed(self, callback: Callable[..., None]):
        self._on_failed = callback

    def is_complete(self) -> bool:
        return self._state in [self.SUCCESS, self.FAILED]

    def set_state(self, state):
        if state == self.SUCCESS:
            self._state = self.SUCCESS
            self.on_success(self)
            if self._must_reset:
                self._reinit()
        elif state == self.FAILED:
            self._state = self.FAILED
            self.on_failed(self)
            if self._must_reset:
                self._reinit()
        elif state == self.STARTED:
            self._starttime = time.time()
            self._state = self.STARTED

    def success(self) -> bool:
        return self._state == self.SUCCESS

    def failed(self) -> bool:
        return self._state == self.FAILED

    def __str__(self) -> str:
        return "LogEvent instance: ({}) -> ({})\nLOGS:\n{}".format(
            self.sr.pattern, (self.er and self.er.pattern), "".join(self.loglines)
        )

    def __repr__(self) -> str:
        SUCCESS = "\x1b[42SUCCESS\x1b[0m"
        FAIL = "\x1b[41mFAIL\x1b[0m"
        TITLE = "\x1b[1m" + self.title + "\x1b[0m"

        result = []

        if self.success():
            result.append(SUCCESS + ": " + TITLE)

        elif self.failed():
            result.append(FAIL + ": " + TITLE)
        else:
            result.append(["WAITING", "IN PROGRESS"][self._state] + ": " + TITLE)
        if self.er:
            end_pat = f"-> ({self.er.pattern})"
        else:
            end_pat = ""
        result.append(f"Patterns: ({self.sr.pattern}) {end_pat}")
        if hasattr(self, "reason"):
            result.append("Reason: " + self.reason)
        return "\n".join(result)


def attach_events(log_file: str, events: List[LogEvent]):
    try:
        # lazy generator that will yield a line of text when available
        for line in tail("-f", log_file, _iter=True):
            print("Reading: " + line)
            for e in events:
                if not e.is_complete():
                    e.process(line)
            # Exit if all events are done
            if all([e.is_complete() for e in events]):
                return

    except KeyboardInterrupt:
        return
