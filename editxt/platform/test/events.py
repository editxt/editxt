import logging
import threading
from functools import wraps

log = logging.getLogger(__name__)

def call_later(delay, callback, *args, **kw):
    log.warn("calling immediately (not after delay of %s)", delay)
    callback(*args, **kw)

def call_in_main_thread(_callback, *args, **kw):
    log.warn("calling in thread: %s",  threading.current_thread().name)
    _callback(*args, **kw)

def call_in_thread(_target, *args, **kw):
    log.warn("not calling in thread: %s", _target)
    _target(*args, **kw)

def debounce(delay=0.1, coalesce_args=lambda *a, **k:(a, k)):
    def decorator(fn):
        @wraps(fn)
        def debounced(*args, **kw):
            args, kw = coalesce_args(*args, **kw)
            fn(*args, **kw)
        return debounced
    if callable(delay):
        delay, fn = 0.1, delay
        return decorator(fn)
    return decorator
