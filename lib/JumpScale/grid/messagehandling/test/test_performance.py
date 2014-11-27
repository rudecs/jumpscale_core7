import time

from JumpScale import j

if not q._init_called:
    from JumpScale.core.InitBaseCore import q


def logtest(total, interval, message, format=False):
    j.core.messagehandler3.connect2localLogserver()

    start = time.time()
    result = []

    for n in range(1, total + 1):
        if n % interval == 0:
            t = time.time()
            delta = t - start
            print(("Did %d of %d logs in %ss" % (n, total, delta)))
            result.append({
                "done": n,
                "time": delta
            })

        if format:
            data = {
                "n": n,
                "total": total
            }
            j.logger.log(message % data)
        else:
            j.logger.log(message)

    totalTime = time.time() - start
    average = total / float(totalTime)
    print(("Logged %d messages at %f messages per second on average" % (total,
                                                                       average)))
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test the logging system")
    parser.add_argument("--message", help="The message to log, can include "
                        "%(n)s and %(total)s if you enable formatting", default="Testing 1 2 3")
    parser.add_argument("--format", action="store_true",
                        help="Message contains formatting")
    parser.add_argument("--total", type=int, default=10000,
                        help="The total amount of log calls that should happen")
    parser.add_argument("--interval", type=int, default=1000,
                        help="The interval to print the passed time")

    parser.add_argument("--zeromq", action="store_true",
                        help="Enable the 0MQ log handler")
    parser.add_argument("--dump-json", dest="dumpjson",
                        type=argparse.FileType('w'))

    args = parser.parse_args()

    result = logtest(args.total, args.interval, args.message, args.format)
