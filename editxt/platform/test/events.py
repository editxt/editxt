import logging

log = logging.getLogger(__name__)

def call_later(delay, callback, *args, **kw):
    log.warn("calling immediately (not after delay of %s)", delay)
    callback(*args, **kw)
