from logan import LogEvent, attach_events
import re


def print_result(e: LogEvent):
    SUCCESS = "\x1b[42m"
    FAIL = "\x1b[1;41m"
    BOLD = "\x1b[1m"
    END = "\x1b[0m"
    if e.success():
        print(f"{SUCCESS}Success{END}: {BOLD}{e.title}{END}")
        print(f"Patterns: ({e.sr.pattern}) -> ({e.er and e.er.pattern})")
        print("".join(e.loglines))
    else:
        print(f"{FAIL}Fail{END}: {BOLD}{e.title}{END}")
        print(f"Patterns: ({e.sr.pattern}) -> ({e.er and e.er.pattern})")
        print(f"Reason: {e.reason}")


if __name__ == "__main__":

    def print_ok(event: LogEvent):
        print(event.sr.pattern + ": ok")

    p_process = re.compile("process")
    p_success = re.compile("success")

    e1 = LogEvent(p_process, p_success, title="Test flow")
    e2 = LogEvent(re.compile("this pattern does not exist"), title="Must fail")
    e3 = LogEvent(p_success)

    events = [e1, e2, e3]
    for e in events:
        e.on_success = print_ok
    attach_events("test.log", events)

    for e in events:
        print_result(e)
