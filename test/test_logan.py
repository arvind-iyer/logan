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

    e_success = logan.LogEvent(p_process, p_success, title="Test flow")
    e_success.on_success = print_result
    logman.register_event(e_success)

    e_duration = logan.LogEvent(p_duration, title="Duration")
    e_duration.on_success = print_result
    logman.register_event(e_duration)

    e_proc = logan.LogEvent(re.compile("this line does not exist 123123"), timeout=1)

    def delete_event(e):
        print("Current events:")
        [print(event.title) for event in logman._events]
        print("Deleting: " + e.title)
        logman.remove_event(e)
        print()

    e_proc.on_failed = delete_event
    logman.register_event(e_proc)

    logman.listen(args.logfile, follow=args.follow)

    for e in logman._events:
        print(e.title)
