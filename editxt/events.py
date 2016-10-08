# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2016 Daniel Miller <millerdev@gmail.com>
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
from functools import partial

import AppKit as ak
from editxt.util import WeakProperty


def eventize(obj):
    """Event connection setup helper

    Usage:

    class Obj:
        class events:
            some_action = eventize.attr("obj.path.to.do_some_action")
            other_action = eventize.call("obj.path.to.setup_other_action")

        def __init__(self):
            self.obj = ObjectThatCallsBackOnEvents()

            # Sets event callback at obj.path.to.do_some_action and
            # calls obj.path.to.setup_other_action(event_callback)
            eventize(self)

        def when_action_happens(self):
            self.obj.path.to.do_some_action("the arg")

    def do_something(arg):
        "arg is specifc to the 'some_action' event"

    def do_other(arg):
        "arg is specifc to the 'other_action' event"

    obj = Obj()
    obj.on = eventize(obj)
    obj.on.some_action(do_something)
    obj.on.other_action(do_other)
    """
    if hasattr(obj, "on"):
        raise RuntimeError("%r already has 'on' attribute")
    if not hasattr(obj, "events"):
        raise RuntimeError("%s has no 'events' property")
    if isinstance(obj, ak.NSObject):
        # HACK work around TypeError: cannot create weak reference ...
        obj.on = ObjcEventConnector(obj)
    else:
        obj.on = EventConnector(obj)


def attr(path):
    """Register callback on object by setting a callback attribute

    The event callback is only set on the object if and when an event
    listener is attached. It is required that the attribute has an
    initial value of `None` (it will be overwritten when an event
    listener is attached). This allows for the event producer to
    efficiently skip all event dispatching if no listeners are
    configured.
    """
    def setup_event(name, obj, callback):
        orig = obj
        if "." in path:
            parts = path.split('.')
            parts, attr = parts[:-1], parts[-1]
            for part in parts:
                obj = getattr(obj, part)
        else:
            attr = path
        try:
            dispatchers = obj.__eventize_dispatchers
        except AttributeError:
            dispatchers = obj.__eventize_dispatchers = {}
        try:
            dispatch = dispatchers[path]
        except KeyError:
            dispatch = dispatchers[path] = _make_dispatch()
            try:
                current_attr = getattr(obj, attr)
            except AttributeError:
                raise RuntimeError("attr not found: %s.%s" % (orig, path))
            if getattr(obj, attr) is not None:
                raise NotImplementedError(
                    "cannot add multiple '%s' listeners" % name)
            setattr(obj, attr, dispatch)
        dispatch.callbacks.append(callback)
    return setup_event


def call(path, dispatch=True):
    """Register event callback on object by calling a method

    The method identified by `path` is only called if and when an event
    listener is attached.
    """
    def setup_event(name, obj, callback):
        if "." in path:
            parts = path.split('.')
            parts, method_name = parts[:-1], parts[-1]
            for part in parts:
                obj = getattr(obj, part)
        else:
            method_name = path
        if not dispatch:
            getattr(obj, method_name)(callback)
            return
        try:
            dispatchers = obj.__eventize_dispatchers
        except AttributeError:
            dispatchers = obj.__eventize_dispatchers = {}
        try:
            dispatcher = dispatchers[path]
        except KeyError:
            dispatcher = dispatchers[path] = _make_dispatch()
            getattr(obj, method_name)(dispatcher)
        dispatcher.callbacks.append(callback)
    return setup_event


def _make_dispatch():
    callbacks = []
    def dispatch(*args, **kw):
        for callback in callbacks:
            callback(*args, **kw)
    dispatch.callbacks = callbacks
    return dispatch


#def proxy(obj, delegate):
#    if hasattr(obj, "on"):
#        raise RuntimeError("%r already has 'on' attribute")
#    obj.on = Proxy(delegate.on)


eventize.attr = attr
eventize.call = call
#eventize.proxy = proxy


class EventConnector:

    _obj = WeakProperty()

    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        setup_event = getattr(self._obj.events, name)
        return partial(setup_event, name, self._obj)


class ObjcEventConnector(EventConnector):

    _obj = None


#class Proxy:
#
#    def __init__(self, delegate):
#        self._delegate = delegate
#
#    def __getattr__(self, name):
#        return getattr(self._delegate, name)
