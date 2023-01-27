import pjsua2 as pj
from datetime import datetime
import traceback
import sys

isquit = False


def quitPJSUA():
    isquit = True


def sleep4PJSUA2(t):
    """sleep for a perid time, it takes care of pjsua2's threading,
    if the isquit is True, this function would immediately quit.

    Args:
        t (int): The time(second) you wants to sleep.
            if t equal -1, then it would sleep forever.
    """

    global isquit

    start = datetime.now()
    end = start
    if t == -1:
        while True:
            pj.Endpoint.instance().libHandleEvents(20)
    else:
        while (end - start).total_seconds() < t:
            end = datetime.now()
            pj.Endpoint.instance().libHandleEvents(20)
    return (end - start).total_seconds()


def handleErr(e: pj.Error):
    """handle the error, it would print pj error and exit the PJSUA
        arg:
            e: pj.Error
    """
    print("Exception {}\r\n, Traceback:\r\n".format(e.info()))
    traceback.print_exception(*sys.exc_info())
    quitPJSUA()
