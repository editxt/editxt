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
import objc
import Foundation as fn

from mocker import ANY, expect, Mocker

import editxt.platform.kvo as mod
from editxt.datatypes import WeakProperty
from editxt.test.util import assert_raises, eq_, TestConfig


def test_create_kvolist():
    lst = mod.KVOList()
    eq_(len(lst.items()), 0)

def test_kvolist_items():
    lst = mod.KVOList()
    newitems = fn.NSMutableArray.alloc().init()
    lst.setItems_(newitems)
    eq_(lst.items(), newitems)

def test_kvolist_items():
    class Proxy(object):
        target = WeakProperty()
        def __init__(self, target):
            self._target = target
        def __repr__(self):
            return "Proxy({!r})".format(self._target)
    class KVObject(object):
        def __init__(self, name):
            self.name = name
            self.proxy = Proxy(self)
        def __repr__(self):
            return "ob{}".format(self.name)
    lst = mod.KVOList()
    ob1 = KVObject(1)
    ob2 = KVObject(2)
    ob3 = KVObject(3)
    ob4 = KVObject(4)
    ob5 = KVObject(5)
    ob6 = KVObject(6)

    # test KVO methods
    yield do_kvolist_countOfItems, lst, 0
    yield do_kvolist_insertObject_inItemsAtIndex_, lst, ob1, 0
    yield do_kvolist_countOfItems, lst, 1
    yield do_kvolist_objectInItemsAtIndex_, lst, ob1, 0
    yield do_kvolist_replaceObjectInItemsAtIndex_withObject_, lst, ob2, 0
    yield do_kvolist_objectInItemsAtIndex_, lst, ob2, 0
    yield do_kvolist_removeObjectFromItemsAtIndex_, lst, 0
    yield do_kvolist_countOfItems, lst, 0

    # test list convenience methods
    yield do_kvolist_len, lst, 0
    yield do_kvolist_insert, lst, ob1, 0
    yield do_kvolist_len, lst, 1
    yield do_kvolist_getitem, lst, ob1, 0
    yield do_kvolist_setitem, lst, ob2, 0
    yield do_kvolist_append, lst, ob1
    yield do_kvolist_delitem, lst, 1
    yield do_kvolist_contains, lst, ob2
    yield do_kvolist_not_contains, lst, ob1
    yield do_kvolist_count, lst, ob1, 0
    yield do_kvolist_count, lst, ob2, 1
    yield do_kvolist_extend, lst, [ob3, ob4]
    eq_(len(lst), 3)
    yield do_kvolist_index, lst, ob2, 0
    yield do_kvolist_iter, lst
    yield do_kvolist_remove, lst, ob2
    yield do_kvolist_remove_nonexistent, lst, ob1
    yield do_kvolist_pop, lst, 1
    eq_(list(lst), [ob3])
    yield do_kvolist_pop, lst
    eq_(list(lst), [])

    lst = mod.KVOList([ob1, ob2, ob3, ob4])
    yield do_kvolist_getslice, lst, 1, 3, [ob2, ob3]

    lst = mod.KVOList([ob1, ob2, ob3, ob4])
    yield do_kvolist_setslice, lst, 1, 3, [ob5, ob6], [ob1, ob5, ob6, ob4]

    lst = mod.KVOList([ob1, ob2, ob3, ob4])
    yield do_kvolist_delslice, lst, 1, 3, [ob1, ob4]

def do_kvolist_countOfItems(lst, num):
    eq_(lst.countOfItems(), num)

def do_kvolist_insertObject_inItemsAtIndex_(lst, obj, index):
    lst.insertObject_inItemsAtIndex_(obj, index)
    assert lst.items()[index] is obj

def do_kvolist_objectInItemsAtIndex_(lst, obj, index):
    assert lst.objectInItemsAtIndex_(index) is obj

def do_kvolist_removeObjectFromItemsAtIndex_(lst, index):
    lst.removeObjectFromItemsAtIndex_(index)

def do_kvolist_replaceObjectInItemsAtIndex_withObject_(lst, obj, index):
    lst.replaceObjectInItemsAtIndex_withObject_(index, obj)

def do_kvolist_len(lst, num):
    eq_(len(lst), num)

def do_kvolist_insert(lst, obj, index):
    lst.insert(index, obj)
    assert lst[index] is obj

def do_kvolist_getitem(lst, obj, index):
    assert lst[index] is obj

def do_kvolist_setitem(lst, obj, index):
    lst[index] = obj
    assert lst[index] is obj

def do_kvolist_delitem(lst, index):
    del lst[index]

def do_kvolist_contains(lst, obj):
    assert obj in lst

def do_kvolist_not_contains(lst, obj):
    assert obj not in lst

def do_kvolist_append(lst, obj):
    lst.append(obj)
    assert lst[-1] is obj, (lst[-1], obj)

def do_kvolist_extend(lst, objs):
    offset = len(lst)
    lst.extend(objs)
    for i in range(len(objs)):
        assert lst[offset + i] is objs[i]

def do_kvolist_index(lst, obj, index):
    eq_(lst.index(obj), index)
    assert lst[index] is obj

def do_kvolist_iter(lst):
    items = []
    for it in lst:
        items.append(it)
    eq_(len(items), len(lst))
    for i, it in enumerate(items):
        assert lst[i] is it

def do_kvolist_remove(lst, obj):
    assert obj in lst, "%s is not in list (cannot test remove)" % (obj,)
    lst.remove(obj)
    assert obj not in lst

def do_kvolist_remove_nonexistent(lst, obj):
    assert obj not in lst, "%s is in list (cannot test remove nonexistent)" % (obj,)
    try:
        lst.remove(obj)
        raise Exception("obj was removed from list, but should not have been")
    except ValueError:
        pass

def do_kvolist_pop(lst, *args):
    len_before_pop = len(lst)
    if args:
        eq_(len(args), 1, "too many arguments for pop([index])")
        item = lst[args[0]]
    else:
        item = lst[-1]
    popped = lst.pop(*args)
    assert item is popped, (item, popped)
    eq_(len(lst), len_before_pop - 1)

def do_kvolist_count(lst, obj, num):
    eq_(lst.count(obj), num)

def do_kvolist_getslice(lst, i, j, val):
    eq_(lst[i:j], val)

def do_kvolist_setslice(lst, i, j, ins, val):
    lst[i:j] = ins
    eq_(list(lst), val)

def do_kvolist_delslice(lst, i, j, val):
    del lst[i:j]
    eq_(list(lst), val)


def test_KVOProxy():
    mod.KVOProxy(Mocker().mock()) # cache the proxy class to avoid side affects
    def run(test):
        m = Mocker()
        target = m.mock()
        proxy = mod.KVOProxy(target)
        test(m, target, proxy)
    def test_get_missing(m, target, proxy):
        expect(target.thekey).throw(AttributeError)
        with m:
            assert_raises(AttributeError, lambda:proxy.thekey)
    def test_set_missing(m, target, proxy):
        expect(target.thekey).throw(AttributeError)
        value = target.thekey = "<value>"
        with m:
            proxy.thekey = value
    def test_get(m, target, proxy):
        value = target.thekey >> "<value>"
        with m:
            eq_(proxy.thekey, value)
    def test_set(m, target, proxy):
        with m.order():
            before = target.thekey >> "<before>"
            after = target.thekey = "<after>"
        with m:
            proxy.thekey = after
    def test_set_matching(m, target, proxy):
        value = target.thekey >> "<value>"
        with m:
            proxy.thekey = value
    def test_proxy_proxy(m, target, proxy):
        with m, assert_raises(AttributeError,
                msg="{} has no attribute 'proxy'".format(type(proxy).__name__)):
            proxy.proxy
    yield run, test_get_missing
    yield run, test_set_missing
    yield run, test_get
    yield run, test_set
    yield run, test_set_matching
    #yield run, test_proxy_proxy


def test_KVOLink():
    def test(c):
        m = Mocker()
        links = []
        for path, key in c.lks:
            obj = m.mock()
            subj = m.mock()
            links.append((obj, path, subj, key))
            obj.addObserver_forKeyPath_options_context_(ANY, path, 0, ANY)
            obj.removeObserver_forKeyPath_(ANY, path)
        with m:
            link = mod.KVOLink(links)
            link.close()
    c = TestConfig()
    yield test, c(lks=[])
    yield test, c(lks=[("path.to.key", "other_key")])
    yield test, c(lks=[("path.to.key1", "other_key"), ("path.to.key2", "other_key")])

class KVOLinkItem(fn.NSObject):
    @objc.namedSelector(b"init:subject:")
    def init(self, key, subj):
        super(KVOLinkItem, self).init()
        setattr(self, key, None)
        self.subj = subj
        self.proxy = mod.KVOProxy(self)
        return self
    def _set_path(self, value):
        self.subj.key = value
    def _get_path(self):
        return self.subj.key

class KVOLinkTester(fn.NSObject):
    was_notified = False
    def observeValueForKeyPath_ofObject_change_context_(self, path, obj, change, context):
        self.was_notified = True

def test_KVOLink_in_action():
    subj = KVOLinkItem.alloc().init("key", None)
    subj.key = "<old>"
    tester = KVOLinkTester.alloc().init()
    subj.addObserver_forKeyPath_options_context_(tester, "key", 0, 1000)
    obj = KVOLinkItem.alloc().init("path", subj)
    link = mod.KVOLink([(obj, "path", subj, "key")])
    assert not tester.was_notified
    obj.proxy.path = "<new>"
    assert tester.was_notified
