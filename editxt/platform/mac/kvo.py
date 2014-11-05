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
from contextlib import contextmanager
from itertools import count
from weakref import WeakKeyDictionary

import objc
import Foundation as fn

from editxt.datatypes import AbstractNamedProperty, WeakProperty


class KVOList(fn.NSObject):
    """A list with Key Value Observing items

    Items inserted into the list must have a ``proxy`` attribute that
    returns a KVO-compliant version of the item. A list of proxied items
    is exposed through the ``items`` property, and un-proxied items
    (obtained with ``proxy_target(proxy)``) are exposed through the
    Python list-like interface of this object. It is expected that the
    ``proxy`` property for any given object always returns the same
    proxy instance.
    """

    def __new__(cls, items=None):
        value = cls.alloc().init()
        if items is not None:
            value.extend(items)
        return value

    def init(self):
        super(KVOList, self).init()
        self._items = fn.NSMutableArray.alloc().init()
        return self

    def dealloc(self):
        del self._items[:]
        self._items = None
        super().dealloc()

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
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        return proxy_target(self._items[index])

    def __setitem__(self, index, obj):
        if isinstance(index, slice):
            self.mutableArrayValueForKey_("items")[index] = [
                proxy(item) for item in obj]
        else:
            self.mutableArrayValueForKey_("items")[index] = proxy(obj)

    def __delitem__(self, index):
        del self.mutableArrayValueForKey_("items")[index]

    def __contains__(self, obj):
        return proxy(obj) in self._items

    def __iter__(self):
        return (proxy_target(item) for item in self._items)

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, list(self))

    def append(self, obj):
        self.mutableArrayValueForKey_("items").append(proxy(obj))

    def extend(self, items):
        self.mutableArrayValueForKey_("items").extend(
            proxy(item) for item in items)

    def index(self, obj):
        return self._items.index(proxy(obj))

    def insert(self, index, obj):
        self.mutableArrayValueForKey_("items").insert(index, proxy(obj))

    def remove(self, obj):
        self.mutableArrayValueForKey_("items").remove(proxy(obj))

    def pop(self, item=None):
        args = () if item is None else (item,)
        return proxy_target(self.mutableArrayValueForKey_("items").pop(*args))

    def count(self, item):
        return list(self).count(item)

#    def count(self, item=None):
#        """Count the occurrences of the first argument given or count
#        the total number of items in the list if no args are supplied.
#        """
#        if item is not None:
#            # HACK inefficient, but necessary because NSMutableArray.count() takes no arguments
#            return list(self._items).count(item)
#        return self._items.count()


class KVOProxy(fn.NSObject):
    """Key-value observing proxy for plain Python objects

    http://www.cocoarocket.com/articles/kvodependent.html
    """

    NA = object()

    def __new__(cls, target, _registry={}):
        try:
            proxy_class = _registry[type(target)]
        except KeyError:
            dependent_key_paths = getattr(target, "dependent_key_paths", {})
            def keyPathsForValuesAffectingValueForKey_(cls, key):
                return fn.NSSet.setWithArray_(dependent_key_paths.get(key, []))
            name = "{}_{}".format(cls.__name__, type(target).__name__)
            members = {
                "keyPathsForValuesAffectingValueForKey_":
                    classmethod(keyPathsForValuesAffectingValueForKey_),
            }
            #type_ = WeakKVOProxy if weakref else KVOProxy
            proxy_class = type(name, (cls,), members)
            _registry[type(target)] = proxy_class
        return proxy_class.alloc().init_(target)

    def init_(self, target):
        self = super().init()
        self.__dict__["_target"] = target
        return self

    def dealloc(self):
        self.__dict__.pop("_target", None)
        super().dealloc()

    # probably not needed since we have no concrete accessors
    def automaticallyNotifiesObserversForKey_(self, key):
        return False

    def valueForKey_(self, key):
        return getattr(self._target, key)

    def setValue_forKey_(self, value, key):
        if value != getattr(self._target, key, self.NA):
            with kvo_change(self, key):
                setattr(self._target, key, value)

    def __getattr__(self, key):
        return getattr(self._target, key)

    def __setattr__(self, key, value):
        if value != getattr(self._target, key, self.NA):
            with kvo_change(self, key):
                setattr(self._target, key, value)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._target == other._target
        if isinstance(other, type(self._target)):
            return other == self._target
        return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._target)

    def __iter__(self):
        return iter(self._target)

    def __repr__(self):
        return "<{} {!r}>".format(type(self).__name__, self._target)


def proxy_target(proxy):
    """Retrieve the proxied object"""
    return proxy._target


def proxy(item):
    """Retrieve the proxy from the given object"""
    return item if isinstance(item, KVOProxy) else item.proxy


#class WeakKVOProxy(KVOProxy):
#
#    _target = WeakProperty()
#
#    def init_(self, target):
#        self = super(_KVOProxy, self).init()
#        type(self)._target.__set__(self, target)
#        return self


@contextmanager
def kvo_change(obj, key):
    obj.willChangeValueForKey_(key)
    try:
        yield
    finally:
        obj.didChangeValueForKey_(key)


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
            context = next(self.keygen)
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


class _KVOLink(fn.NSObject):

    @objc.namedSelector(b"init:")
    def init(self, subjects):
        self = super(_KVOLink, self).init()
        self.subjects = subjects
        return self

    def observeValueForKeyPath_ofObject_change_context_(self, path, obj, change, context):
        subject, key = self.subjects[context]
        subject.willChangeValueForKey_(key) # hmmm... will this work? it seems to
        subject.didChangeValueForKey_(key)
