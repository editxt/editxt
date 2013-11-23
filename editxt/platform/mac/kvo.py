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
from itertools import count

import objc
import Foundation as fn

from editxt.datatypes import WeakProperty


def KVOList():
    return _KVOList.alloc().init()


class _KVOList(fn.NSObject):

    def init(self):
        super(_KVOList, self).init()
        self._items = fn.NSMutableArray.alloc().init()
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
        return '<%s %r>' % (type(self).__name__, list(self))

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

KVOList.alloc = _KVOList.alloc # DEPRECATED


def KVOProxy(target, weakref=False, _registry={}):
    # http://www.cocoarocket.com/articles/kvodependent.html
    try:
        proxy_class = _registry[type(target)]
    except KeyError:
        dependent_key_paths = getattr(target, "dependent_key_paths", {})
        def keyPathsForValuesAffectingValueForKey_(cls, key):
            return fn.NSSet.setWithArray_(dependent_key_paths.get(key, []))
        name = "%s_KVOProxy" % type(target).__name__
        members = {
            "keyPathsForValuesAffectingValueForKey_":
                classmethod(keyPathsForValuesAffectingValueForKey_),
        }
        type_ = _WeakKVOProxy if weakref else _KVOProxy
        proxy_class = type(name, (type_,), members)
        _registry[type(target)] = proxy_class
    return proxy_class.alloc().init_(target)


class _KVOProxy(fn.NSObject):

    NA = object()

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

    def __iter__(self):
        return iter(self._target)


class _WeakKVOProxy(_KVOProxy):

    _target = WeakProperty()

    def init_(self, target):
        self = super(_KVOProxy, self).init()
        type(self)._target.__set__(self, target)
        return self


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
