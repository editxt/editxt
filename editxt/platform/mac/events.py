import AppKit as ak

def call_later(delay, callback, *args, **kw):
    call = DelayedCall.alloc().init_args_kw_(callback, args, kw)
    call.performSelector_withObject_afterDelay_("do", call, delay)

_CALLS = {}

class DelayedCall(ak.NSObject):

    def init_args_kw_(self, callback, args, kw):
        _CALLS[id(self)] = self
        self.callback = callback
        self.args = args
        self.kw = kw
        return self

    def do(self):
        self.callback(*self.args, **self.kw)
        _CALLS.pop(id(self))
