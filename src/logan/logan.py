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
    _subber = re.compile(r"`(\d+)`")

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

        Args:
            start_regex(re.Pattern): can be created by calling re.compile() on a regular expression.
                If the current log line matches this, a timer is started and
                we attempt to match for the end_regex expression.
            end_regex(re.Pattern): [Optional] After the start_regex is found,
                we will attempt to match with this pattern(if provided).
                If not provided, the status is immediately set to SUCCESS.
                If provided and this pattern is found within the timeout period,
                the event is a success, else fail.
            timeout(float): Timeout period in seconds
            autoreset(float): On completion of event, this will immediately
                reset the instance and begin looking for the start_regex again.
                Useful if the callbacks are set and are used to trigger
                external activity.
        """
        self.sr = start_regex
        self.er = end_regex
        self.timeout = timeout
        self.loglines: List[str] = []
        self._matches = None

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
            self._reason = "Timed out"
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
    def reason(self) -> str:
        if self._state == self.SUCCESS:
            return ""
        if hasattr(self, "_reason"):
            return self._reason
        elif self._state == self.STARTED:
            return "End pattern not found"
        elif self._state == self.WAITING:
            return "Start pattern not found"

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
        SUCCESS = "SUCCESS\x1b[0m"
        FAIL = "FAIL"
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
        if self.reason:
            result.append("Reason: " + self.reason)
        if self._matches:
            result.append(f"Groups: {self._matches}")
        return "\n".join(result)


def attach_events(log_file: str, events: List[LogEvent], follow=True):
    """
    Read a log file and listen for LogEvents.

    Params:
        log_file (str): Path to a plain-text log file
        events (LogEvent[]): List of instances of logan.LogEvent
        follow: If true, will imitate the behavior of 'tail -f' on the file
            and read new lines of text when made available.
            else, will read the text file until the last line and exit
    """
    try:
        if follow:
            # lazy generator that will yield a line of text when available
            log_lines_iter = tail("-f", log_file, _iter=True)
        else:
            with open(log_file, "r") as f:
                log_lines_iter = f.readlines()

        for line in log_lines_iter:
            for e in events:
                if not e.is_complete():
                    e.process(line)
            # Exit if all events are done
            if all([e.is_complete() for e in events]):
                return

    except KeyboardInterrupt:
        return
