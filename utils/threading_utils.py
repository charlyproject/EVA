import threading


def submit_background_task(func, *args, name="", **kwargs):
    t = threading.Thread(target=func, args=args, daemon=True, name=name)
    t.start()
    return t


def submit_task(func, *args, priority=None, name="", **kwargs):
    return submit_background_task(func, *args)


class ThreadPriority:
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
