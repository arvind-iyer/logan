import re
import logan
import argparse


def print_result(e: logan.LogEvent):
    SUCCESS = "\x1b[42m"
    FAIL = "\x1b[1;41m"
    BOLD = "\x1b[1m"
    END = "\x1b[0m"
    if e.success():
        print(
            "{SUCCESS}Success{END}: {BOLD}{title}{END}".format(
                SUCCESS=SUCCESS, BOLD=BOLD, END=END, title=e.title
            )
        )
        print("Patterns: ({}) -> ({})".format(e.sr.pattern, e.er and e.er.pattern))
        print("".join(e.loglines))
    else:
        print(
            "{FAIL}Fail{END}: {BOLD}{title}{END}".format(
                FAIL=FAIL, BOLD=BOLD, END=END, title=e.title
            )
        )
        print("Patterns: ({}) -> ({})".format(e.sr.pattern, e.er and e.er.pattern))
        print("Reason: " + e.reason)
    if e._matches:
        print("Groups: " + str(e._matches))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("logfile", type=str, help="path to log file")
    ap.add_argument("--follow", "-f", action="store_true")
    args = ap.parse_args()
    print(args)
    p_process = re.compile("process")
    p_success = re.compile("success")
    p_duration = re.compile(r"(\d+\.?\d+) seconds")

    logman = logan.Manager()

    # Test a simple start -> stop flow
    e_success = logan.LogEvent(p_process, p_success, title="Test flow")
    e_success.on_success = print_result
    logman.register_event(e_success)

    # Test a start only event
    e_duration = logan.LogEvent(p_duration, title="Test single")
    e_duration.on_success = print_result
    logman.register_event(e_duration)

    # Test pattern substitution
    e_patterns = logan.LogEvent(
        re.compile("execution: ([\w\d_-]+)"),
        re.compile("Returning with \w+ for `0`"),
        title="Test pattern subsitution",
    )
    logman.register_event(e_patterns)

    # Test on-the-fly event deletion and intentional failure
    e_proc = logan.LogEvent(re.compile("this line does not exist 123123"), timeout=1)

    def delete_event(e):
        print("Current events:")
        [print(event.title) for event in logman._events]
        print("Deleting event: " + e.title)
        logman.remove_event(e)
        print()

    e_proc.on_failed = delete_event
    logman.register_event(e_proc)

    logman.listen(args.logfile, follow=args.follow)

    success_events = []
    failed_events = []
    for e in logman._events:
        if e.success():
            success_events.append(e.title)
        if e.failed():
            failed_events.append(e.title)
    if success_events:
        print(
            "Events Succeeded ({} / {})".format(
                len(success_events), len(logman._events)
            )
        )
        print("*" * 40)
        for e in success_events:
            print("- " + e)

    print()
    if failed_events:
        print("Events Failed ({} / {})".format(len(failed_events), len(logman._events)))
        print("*" * 40)
        for e in failed_events:
            print("- " + e)
