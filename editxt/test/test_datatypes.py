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
from editxt.datatypes import ContextMap, RecentItemStack, WeakProperty
from editxt.test.util import eq_


def test_create_context_map():
    map = ContextMap()
    eq_(len(map), 0)

def test_context_map_put_and_pop():
    map = ContextMap()
    obj = object()
    key = map.put(obj)
    assert isinstance(key, int)
    eq_(len(map), 1)
    eq_(map.pop(key), obj)
    eq_(len(map), 0)

def test_context_map_pop_non_existent_key():
    map = ContextMap()
    key = 1000
    try:
        value = map.pop(key)
    except KeyError:
        pass
    else:
        raise AssertionError("context map had value %r for key %r" % (value, key))

def test_context_map_pop_with_default():
    map = ContextMap()
    DEF = "default"
    eq_(map.pop(1000, "default"), "default")


def test_recent_items_queue_size():
    ris = RecentItemStack(20)
    eq_(len(ris), 0)
    eq_(ris.max_size, 20)

def test_recent_items_queue_update_and_pop():
    ris = RecentItemStack(4)
    items = [8, 2, 6, 4, 5, 7]
    for item in items:
        ris.push(item)
    eq_(len(ris), 4)
    for item in reversed(items[-4:]):
        eq_(ris.pop(), item)
    eq_(len(ris), 0)

def test_recent_items_pop_empty():
    ris = RecentItemStack(4)
    eq_(len(ris), 0)
    assert ris.pop() is None

def test_recent_items_queue_push_existing():
    ris = RecentItemStack(4)
    ris.push(1)
    ris.push(2)
    ris.push(3)
    eq_(list(ris), [1, 2, 3])
    ris.push(1)
    eq_(list(ris), [2, 3, 1])
    ris.push(3)
    eq_(list(ris), [2, 1, 3])

def test_recent_items_queue_remove():
    ris = RecentItemStack(4)
    ris.push(1)
    ris.push(2)
    eq_(list(ris), [1, 2])
    ris.discard(1)
    eq_(list(ris), [2])

def test_recent_items_queue_reset():
    items = list(range(10))
    ris = RecentItemStack(4)
    ris.reset(items)
    eq_(len(ris), 4)
    eq_(list(ris), items[-4:])
    ris.reset()
    eq_(len(ris), 0)

def test_recent_items_size_zero():
    ris = RecentItemStack(0)
    eq_(list(ris), [])
    ris.push(1)
    eq_(list(ris), [])
    eq_(ris.pop(), None)
