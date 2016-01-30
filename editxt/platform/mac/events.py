from functools import wraps

import AppKit as ak


def call_later(delay, callback, *args, **kw):
    """Call callback with arguments after delay

    :returns: A function that cancels the call if it is called.
    """
    call = DelayedCall.alloc().init_args_kw_(callback, args, kw)
    _CALLS[id(call)] = call
    return call.later(delay)


def debounce(delay=0.1, coalesce_args=lambda *a, **k:(a, k)):
    """Create a debouncing decorator

    Decorated functions will be delayed until the given number of
    seconds has elapsed since the most recent time it was invoked.
    """
    def decorator(fn):
        call = DelayedCall.alloc().init_args_kw_(fn, None, None)
        @wraps(fn)
        def debounced(*args, **kw):
            call.args, call.kw = coalesce_args(*args, **kw)
            debounced.cancel()
            debounced.cancel = call.later(delay)
        debounced.cancel = lambda:None
        return debounced
    if callable(delay):
        delay, fn = 0.1, delay
        return decorator(fn)
    return decorator


_CALLS = {}

class DelayedCall(ak.NSObject):

    def init_args_kw_(self, callback, args, kw):
        self.callback = callback
        self.args = args
        self.kw = kw
        return self

    def later(self, delay):
        self.performSelector_withObject_afterDelay_("do", None, delay)
        return self.cancel

    def cancel(self):
        _CALLS.pop(id(self), None)
        ak.NSObject.cancelPreviousPerformRequestsWithTarget_(self)

    def do(self):
        _CALLS.pop(id(self), None)
        self.callback(*self.args, **self.kw)
