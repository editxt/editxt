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
from collections import deque
from itertools import count
from weakref import ref


class ContextMap(object):

    NA = object()

    def __init__(self):
        self.keygen = count()
        self.map = {}

    def __len__(self):
        return len(self.map)

    def put(self, obj):
        key = next(self.keygen)
        self.map[key] = obj
        return key

    def pop(self, key, default=NA):
        if default is ContextMap.NA:
            return self.map.pop(key)
        return self.map.pop(key, default)


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


class AbstractNamedProperty(object):
    """An abstract base class for properties that need to lookup the name
    of the attribute in which they are stored
    """

    def name(self, obj):
        try:
            return self._name
        except AttributeError:
            self._name = "_{}__{}".format(type(self).__name__, next(attr
                for class_ in type(obj).__mro__
                for attr, value in class_.__dict__.items()
                if value is self))
        return self._name


class WeakProperty(AbstractNamedProperty):
    """A property that maintains a weak reference to its vaule"""

    def __get__(self, obj, type_=None):
        if obj is None:
            return self
        return getattr(obj, self.name(obj))()

    def __set__(self, obj, value):
        weak = ref(value) if value is not None else lambda:None
        obj.__dict__[self.name(obj)] = weak

    def __delete__(self, obj):
        delattr(obj, self.name(obj))
