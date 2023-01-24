import pjsua2 as pj
from datetime import datetime


def sleep4PJSUA2(t):
    """sleep for a perid time, it takes care of pjsua2's threading

    Args:
        t (int): The time(second) you wants to sleep.
                if t equal -1, then it would sleep forever.
    """
    start = datetime.now()
    end = start
    if t == -1:
        while True:
            try: 
                pj.Endpoint.instance().libHandleEvents(1000)
            except Exception:
                pass
    else:
        while (end - start).total_seconds() < t:
            end = datetime.now()
            pj.Endpoint.instance().libHandleEvents(1000)
    return (end - start).total_seconds()
