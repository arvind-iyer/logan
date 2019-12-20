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
    if e._matches:
        print("Groups: " + str(e._matches))


if __name__ == "__main__":

    def print_ok(event: LogEvent):
        print(event.sr.pattern + ": ok")

    p_process = re.compile("process")
    p_success = re.compile("success")
    p_duration = re.compile(r"(\d+\.?\d+) seconds")

    events = []
    # search from line containing 'process' until line containing 'success'
    events.append(LogEvent(p_process, p_success, title="Test flow"))
    # search only for a line containing a floating point number(e.g. 3.0023) followed
    # by the word 'seconds' (e.g. 14.99578 seconds)
    events.append(LogEvent(p_duration))

    for e in events:
        e.on_success = print_ok
    attach_events("test.log", events, follow=False)

    for e in events:
        print_result(e)
