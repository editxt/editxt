# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
#
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
#
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.
import functools
import logging
import os
import random
import re
import string
import sys
import types
from collections import namedtuple
from contextlib import contextmanager

import objc
import yaml
import AppKit as ak
import Foundation as fn
from objc import super

import editxt.constants as const
from editxt.platform.constants import KEY
from editxt.platform.kvo import proxy_target

# DEPRECATED
from editxt.platform.kvo import KVOList, KVOProxy, KVOLink
from editxt.datatypes import ContextMap, RecentItemStack, WeakProperty

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# testing annotation utilities

def untested(*args, **kw):
    if isinstance(args[0], str):
        return message("untested", args[0])
    return message("untested")(*args, **kw)

def refactor(*args, **kw):
    if isinstance(args[0], str):
        return message("refactor", args[0])
    return message("refactor")(*args, **kw)

def message(text, info=""):
    def _message(obj, context=None):
        import editxt
        if "--test" in sys.argv or getattr(editxt, "testing", False):
            description = getattr(obj, "__name__", repr(obj))
            if context is not None:
                ctx = "(context: %s)" % (context,)
            else:
                frame = sys._getframe().f_back.f_back
                name = frame.f_code.co_name
                if name == "<module>":
                    name = frame.f_code.co_filename
                ctx = "(%s:%s)" % (name, frame.f_lineno)
            infotext = (" - " + info) if info else info
            log.info("%s: %s %s%s", text, description, ctx, infotext)
        return obj
    return _message

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# yaml load/dump

def yaml_dumper_loader():
    try:
        from yaml import CSafeDumper as Dumper, CLoader as Loader
    except ImportError:
        log.warn('falling back to non-optimized YAML dumper/loader')
        from yaml import SafeDumper as Dumper, SafeLoader as Loader

    # patch yaml parser so it does not parse leading-zero-ints as octal
    from yaml.resolver import BaseResolver
    SCALAR = BaseResolver.DEFAULT_SCALAR_TAG
    ZERO_FIRST_INT = re.compile(r"^0\d+$")
    # can't use add_implicit_resolver because it adds it as the last resolver
    Loader.yaml_implicit_resolvers['0'].insert(0, (SCALAR, ZERO_FIRST_INT))

    while True:
        yield Dumper, Loader
yaml_dumper_loader = yaml_dumper_loader()

def dump_yaml(*args, **kw):
    kw.setdefault('Dumper', next(yaml_dumper_loader)[0])
    kw.setdefault('indent', 2)
    return yaml.dump(*args, **kw)

def load_yaml(*args, **kw):
    kw.setdefault('Loader', next(yaml_dumper_loader)[1])
    return yaml.load(*args, **kw)

@contextmanager
def atomicfile(path, mode="w", **kw):
    """Open a file for writing

    Atomically overwrites existing file (if any) on exit.
    """
    mode = mode.replace("w", "x")
    assert mode in "xt xb", "invalid mode: {}".format(mode)
    chars = string.ascii_lowercase + string.digits
    ext = "".join(random.choice(chars) for i in range(8))
    temp = path + "-" + ext
    moved = False
    try:
        with open(temp, mode=mode, **kw) as fh:
            yield fh
        os.rename(temp, path)
        moved = True
    finally:
        if not moved:
            os.remove(temp)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def noraise(func):
    """Decorator for functions that should not raise an error

    The decorated function will return None if it raises an exception.
    """
    @functools.wraps(func)
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception:
            log.exception("unexpected error")
    return wrapper

def fetch_icon(path, size=fn.NSMakeSize(16, 16), default_type="txt"):
    if path is None or not os.path.exists(path):
        img = ak.NSWorkspace.sharedWorkspace().iconForFileType_(default_type)
    else:
        img = ak.NSWorkspace.sharedWorkspace().iconForFile_(path)
    img.setSize_(size)
    return img

images = {}

def load_image(name):
    try:
        return images[name]
    except KeyError:
        path = fn.NSBundle.mainBundle().pathForImageResource_(name)
        if path is None:
            raise RuntimeError("image resource not fund: {}".format(name))
        log.debug("loading image: %s", path)
        url = fn.NSURL.fileURLWithPath_(path)
        image = ak.NSImage.alloc().initWithContentsOfURL_(url)
        images[name] = image
        return image

_Stat = namedtuple("_Stat", ["st_size", "st_mtime"])

def filestat(path):
    """Returns a tuple (<st_size>, <st_mtime>) as taken from os.stat

    st_size - file size in bytes
    st_mtime - time of most recent content modification

    This is useful for checking for file modifications.
    """
    try:
        value = os.stat(path)
        return _Stat(value[6], value[8])
    except OSError:
        return None


def user_path(path, home=os.path.expanduser('~')):
    """Return path with user home prefix replaced with ~ if applicable"""
    if os.path.normpath(path).startswith(home + os.sep):
        path = '~' + os.path.normpath(path)[len(home):]
    return path


def short_path(path, editor):
    project_path = editor and editor.project.path
    if project_path:
        norm_path = os.path.normpath(path)
        norm_project = os.path.normpath(project_path)
        if norm_path.startswith(norm_project + os.sep):
            return "..." + norm_path[len(norm_project):]
    return user_path(path)


@untested
def perform_selector(delegate, selector, *args):
    # this is the supported way to call a selector on a delegate:
    # http://article.gmane.org/gmane.comp.python.pyobjc.devel/5563
    getattr(delegate, selector)(*args)


class Invoker(fn.NSObject):
    """NSInvocation factory for python methods"""

    @objc.namedSelector(b"init:")
    def init(self, callback):
        self = super(Invoker, self).init()
        self.callback = callback
        return self

    @classmethod
    def invoke_(cls, inv):
        inv.callback()

def register_undo_callback(undo_manager, callback):
    """Registers any callable as an undo action"""
    inv = Invoker.alloc().init(callback)
    undo_manager.registerUndoWithTarget_selector_object_(Invoker, "invoke:", inv)

def representedObject(node):
    try:
        return proxy_target(node.representedObject())
    except AttributeError:
        return proxy_target(node.observedObject())

def get_color(value, cache={}):
    if isinstance(value, ak.NSColor):
        return value
    value = str(value)
    try:
        return cache[value]
    except KeyError:
        assert COLOR_RE.match(value), "invalid color value: %r" % value
        if len(value) == 7:
            value = value[1:]
        r = int(value[:2], 16) / 255.0
        g = int(value[2:4], 16) / 255.0
        b = int(value[4:], 16) / 255.0
        color = cache[value] = ak.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0)
        return color

def hex_value(color):
    """Get hex value of ak.NSColor object"""
    return "{:02X}{:02X}{:02X}".format(
        int(color.redComponent() * 0xFF),
        int(color.greenComponent() * 0xFF),
        int(color.blueComponent() * 0xFF),
    )

def rgb2gray(color):
    """Convert RRGGBB color string to grayscale

    This function uses a weighted average combined with a pure average,
    which happens to convert the Mac OS X selection color (A6CAFE) to
    the secondary selection color (CACACA).
    """
    if len(color) != 6:
        raise ValueError(color)
    r = int(color[:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:], 16)
    wavg = 0.299 * r + 0.587 * g + 0.114 * b
    avg = (r + b + g) / 3
    gray = int((wavg + avg) / 2)
    return "{:02X}".format(gray) * 3

COLOR_RE = re.compile("^#?[0-9a-f]{6}$", re.IGNORECASE)


def parse_hotkey(hotkey):
    """Parse a hotkey string returning a tuple: `(key, modifier_mask)`"""
    *groups, key = hotkey.split("+")
    modifiers = 0
    for modifier in groups:
        mod = getattr(KEY.Modifier, modifier, None)
        if mod is None:
            return None, 0
        modifiers |= mod
    if len(key) > 1:
        key = getattr(KEY, key, None)
    return key, modifiers

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Error(Exception): pass

class KVOManager(object):
    """Callback manager for python classes that wish to do KVO

    Example usage:
    class MyKVOClass(kvc):
        kvo = KVOManager()
        def __init__(self):
            super(MyKVOClass, self).__init__(fn.NSObject.alloc().init())
            self.kvo.activate_observers(self)
        @kvo.observe("someKeyPath")
        def someKeyPathCallback(self, oldvalue, newvalue):
            # note: newvalue and oldvalue are optional and will not be
            # passed to this callback if they are not defined as arguments.
            # oldvalue must always be the second argument if present
            # newvalue must always be the third argument if present
            log.info("someKeyPath changed: %s -> %s", oldvalue, newvalue)
    """
    # TODO test

    def __init__(self):
        self.observers = []
    def observe(self, keypath, options=None):
        def observer_maker(func):
            observer = CallbackObserver.alloc() \
                .initWithCallback_forKeypath_options_(func, keypath, options)
            self.observers.append(observer)
            return observer
        return observer_maker
    def activate_observers(self, instance):
        for observer in self.observers:
            observer.activate(instance)
    def deactivate_observers(self, instance):
        for observer in self.observers:
            observer.deactivate(instance)

class CallbackObserver(fn.NSObject):
    # TODO test
    def initWithCallback_forKeypath_options_(self, callback, keypath, options):
        self = super(CallbackObserver, self).init()
        self.callback = callback
        self.keypath = keypath
        if options is None:
            options = 0
            try:
                numargs = callback.__code__.co_argcount
            except AttributeError:
                raise Error("cannot determine number of arguments for function: %r\n"
                    "WORKAROUND: use options arg of kvo.observes decorator" % (callback,))
            if numargs > 1:
                options |= fn.NSKeyValueObservingOptionNew
            if numargs > 2:
                options |= fn.NSKeyValueObservingOptionOld
        self.options = options
        callback.__observer = self
        return self
    def activate(self, instance):
        if hasattr(instance, "__pyobjc_object__"):
            instance = instance.__pyobjc_object__
        instance.addObserver_forKeyPath_options_context_(self, self.keypath, self.options, 0)
    def deactivate(self, instance):
        instance.removeObserver_forKeyPath_(self, self.keypath)
    def __call__(self, oldvalue, newvalue):
        raise NotSupported("directly calling observer methods is not supported (yet)")
    def observeValueForKeyPath_ofObject_change_context_(self, path, object, change, context):
        args = [object]
        if self.options & fn.NSKeyValueObservingOptionNew:
            args.append(change[fn.NSKeyValueChangeNewKey])
        if self.options & fn.NSKeyValueObservingOptionOld:
            args.append(change[fn.NSKeyValueChangeOldKey])
        self.callback(*args)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# debugging utilities

def refs(obj, context=""):
    import gc
    log.debug("[context %s] %r is referenced by:", context, obj)
    for o in gc.get_referrers(obj):
        log.debug(repr(o))
        if type(o).__name__ == "frame":
            log.debug("  %r", o.f_locals)
        #log.debug("<%s 0x%x>", type(o), id(o))
