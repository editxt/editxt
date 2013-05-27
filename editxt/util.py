# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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
import logging
import os
import sys
import types

import objc
import yaml
from AppKit import *
from Foundation import *

import editxt.constants as const

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# testing annotation utilities

def untested(*args, **kw):
    if isinstance(args[0], basestring):
        return message("untested", args[0])
    return message("untested")(*args, **kw)

def refactor(*args, **kw):
    if isinstance(args[0], basestring):
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
        from yaml import CDumper as Dumper, CLoader as Loader
    except ImportError:
        log.warn('falling back to non-optimized YAML dumper/loader')
        from yaml import Dumper, Loader
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class KVOList(NSObject):

    def init(self):
        super(KVOList, self).init()
        self._items = NSMutableArray.alloc().init()
        return self

    def items(self):
        return self._items

    def setItems_(self, items):
        self._items[:] = items

    @objc.accessor
    def countOfItems(self):
        return len(self._items)

    @objc.accessor
    def objectInItemsAtIndex_(self, index):
        return self._items[index]

    @objc.accessor
    def insertObject_inItemsAtIndex_(self, obj, index):
        self._items.insert(index, obj)

    @objc.accessor
    def removeObjectFromItemsAtIndex_(self, index):
        del self._items[index]

    @objc.accessor
    def replaceObjectInItemsAtIndex_withObject_(self, index, obj):
        self._items[index] = obj

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, obj):
        self.mutableArrayValueForKey_("items")[index] = obj

    def __delitem__(self, index):
        del self.mutableArrayValueForKey_("items")[index]

    def __setslice__(self, i, j, value):
        self.mutableArrayValueForKey_("items")[i:j] = value

    def __delslice__(self, i, j):
        del self.mutableArrayValueForKey_("items")[i:j]

    def __contains__(self, obj):
        return obj in self._items

    def __iter__(self):
        return iter(self._items)

    def __repr__(self):
        return '<KVOList %r>' % list(self)

    def append(self, obj):
        self.mutableArrayValueForKey_("items").append(obj)

    def extend(self, objs):
        self.mutableArrayValueForKey_("items").extend(objs)

    def index(self, obj):
        return self._items.index(obj)

    def insert(self, index, obj):
        self.mutableArrayValueForKey_("items").insert(index, obj)

    def remove(self, obj):
        self.mutableArrayValueForKey_("items").remove(obj)

    def pop(self, item=None):
        args = () if item is None else (item,)
        return self.mutableArrayValueForKey_("items").pop(*args)

    def count(self, item=None):
        """Count the occurrences of the first argument given or count
        the total number of items in the list if no args are supplied.
        """
        if item is not None:
            # HACK inefficient, but necessary because NSMutableArray.count() takes no arguments
            return list(self._items).count(item)
        return self._items.count()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from collections import deque

class RecentItemStack(object):

    def __init__(self, max_size):
        self.items = deque()
        self.max_size = max_size

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def push(self, item):
        self.discard(item)
        self.items.append(item)
        while len(self.items) > self.max_size:
            self.items.popleft()

    def pop(self):
        try:
            return self.items.pop()
        except IndexError:
            return None

    def discard(self, item):
        while True:
            try:
                self.items.remove(item)
            except ValueError:
                break

    def reset(self, items=()):
        self.items.clear()
        if items:
            for i, item in enumerate(reversed(items)):
                if i < self.max_size:
                    self.items.appendleft(item)
                if i + 1 >= self.max_size:
                    break

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from weakref import WeakValueDictionary

class WeakProperty(property):

    def __init__(self):
        self.refs = WeakValueDictionary()

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        try:
            return self.refs[obj]
        except KeyError:
            raise AttributeError(obj)

    def __set__(self, obj, value):
        self.refs[obj] = value

    def __delete__(self, obj):
        try:
            del self.refs[obj]
        except KeyError:
            raise AttributeError(obj)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from itertools import count

class ContextMap(object):

    NA = object()

    def __init__(self):
        self.keygen = count()
        self.map = {}

    def __len__(self):
        return len(self.map)

    def put(self, obj):
        key = self.keygen.next()
        self.map[key] = obj
        return key

    def pop(self, key, default=NA):
        if default is ContextMap.NA:
            return self.map.pop(key)
        return self.map.pop(key, default)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def fetch_icon(path, size=NSMakeSize(16, 16), default_type="txt"):
    if path is None or not os.path.exists(path):
        img = NSWorkspace.sharedWorkspace().iconForFileType_(default_type)
    else:
        img = NSWorkspace.sharedWorkspace().iconForFile_(path)
    img.setSize_(size)
    return img

images = {}

def load_image(name):
    try:
        return images[name]
    except KeyError:
        path = NSBundle.mainBundle().pathForImageResource_(name)
        log.debug("loading image: %s", path)
        url = NSURL.fileURLWithPath_(path)
        image = NSImage.alloc().initWithContentsOfURL_(url)
        images[name] = image
        return image

def filestat(path):
    """Returns a tuple (<st_size>, <st_mtime>) as taken from os.stat

    st_size - file size in bytes
    st_mtime - time of most recent content modification

    This is useful for checking for file modifications.
    """
    if os.path.exists(path):
        value = os.stat(path)
        return value[6], value[8]
    return None


def user_path(path):
    """Return path with user home prefix replaced with ~ if applicable"""
    home = os.path.expanduser('~')
    if os.path.normpath(path).startswith(home + os.sep):
        path = '~' + os.path.normpath(path)[len(home):]
    return path


@untested
def perform_selector(delegate, selector, *args):
    # this is the supported way to call a selector on a delegate:
    # http://article.gmane.org/gmane.comp.python.pyobjc.devel/5563
    getattr(delegate, selector)(*args)


class Invoker(NSObject):
    """NSInvocation factory for python methods"""

    @objc.namedSelector("init:")
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
        return node.representedObject()
    except AttributeError:
        return node.observedObject()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from collections import defaultdict

def KVOProxy(target, _registry={}):
    # http://www.cocoarocket.com/articles/kvodependent.html
    try:
        proxy_class = _registry[type(target)]
    except KeyError:
        dependent_key_paths = getattr(target, "dependent_key_paths", {})
        def keyPathsForValuesAffectingValueForKey_(cls, key):
            return NSSet.setWithArray_(dependent_key_paths.get(key, []))
        name = "%s_KVOProxy" % type(target).__name__
        members = {
            "keyPathsForValuesAffectingValueForKey_":
                classmethod(keyPathsForValuesAffectingValueForKey_),
        }
        proxy_class = type(name, (_KVOProxy,), members)
        _registry[type(target)] = proxy_class
    return proxy_class.alloc().init_(target)


class _KVOProxy(NSObject):

    NA = object()
    keygen = count()

    def init_(self, target):
        self = super(_KVOProxy, self).init()
        self.__dict__["_target"] = target
        return self

    # probably not needed since we have no concrete accessors
    def automaticallyNotifiesObserversForKey_(self, key):
        return False

    def valueForKey_(self, key):
        return getattr(self._target, key)

    def setValue_forKey_(self, value, key):
        if value != getattr(self._target, key, _KVOProxy.NA):
            self.willChangeValueForKey_(key)
            try:
                setattr(self._target, key, value)
            finally:
                self.didChangeValueForKey_(key)

    def __getattr__(self, key):
        return getattr(self._target, key)

    def __setattr__(self, key, value):
        if value != getattr(self._target, key, _KVOProxy.NA):
            self.willChangeValueForKey_(key)
            try:
                setattr(self._target, key, value)
            finally:
                self.didChangeValueForKey_(key)


class KVOLink(object):
    """Link and propagate KVO notifications

    Example usage:
    link = KVOLink([(obj, "path.to.key", subject, "key"), ...])

    Explanation:
    observers of 'subj.key' will be notified when 'obj.path.to.key' changes.
    """

    keygen = count()

    def __init__(self, observations):
        subjects = {}
        self.observer = observer = _KVOLink.alloc().init(subjects)
        self.observations = observations
        for obj, keypath, subject, subkey in observations:
            context = self.keygen.next()
#             if isinstance(obj, KVOProxy):
#                 obj = obj.__pyobjc_object__
            obj.addObserver_forKeyPath_options_context_(observer, keypath, 0, context)
            subjects[context] = (subject, subkey)

    def close(self):
        if self.observations is not None:
            obs, self.observations = self.observations, None
            for obj, keypath, subject, subkey in obs:
                obj.removeObserver_forKeyPath_(self.observer, keypath)

    def __del__(self):
        self.close()


class _KVOLink(NSObject):

    @objc.namedSelector("init:")
    def init(self, subjects):
        self = super(_KVOLink, self).init()
        self.subjects = subjects
        return self

    def observeValueForKeyPath_ofObject_change_context_(self, path, obj, change, context):
        subject, key = self.subjects[context]
        subject.willChangeValueForKey_(key) # hmmm... will this work? it seems to
        subject.didChangeValueForKey_(key)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Error(Exception): pass

class KVOManager(object):
    """Callback manager for python classes that wish to do KVO

    Example usage:
    class MyKVOClass(kvc):
        kvo = KVOManager()
        def __init__(self):
            super(MyKVOClass, self).__init__(NSObject.alloc().init())
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

class CallbackObserver(NSObject):
    # TODO test
    def initWithCallback_forKeypath_options_(self, callback, keypath, options):
        self = super(CallbackObserver, self).init()
        self.callback = callback
        self.keypath = keypath
        if options is None:
            options = 0
            try:
                numargs = callback.func_code.co_argcount
            except AttributeError:
                raise Error("cannot determine number of arguments for function: %r\n"
                    "WORKAROUND: use options arg of kvo.observes decorator" % (callback,))
            if numargs > 1:
                options |= NSKeyValueObservingOptionNew
            if numargs > 2:
                options |= NSKeyValueObservingOptionOld
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
        if self.options & NSKeyValueObservingOptionNew:
            args.append(change[NSKeyValueChangeNewKey])
        if self.options & NSKeyValueObservingOptionOld:
            args.append(change[NSKeyValueChangeOldKey])
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
