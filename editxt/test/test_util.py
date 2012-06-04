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
from __future__ import with_statement
import logging
import os

import objc
from mocker import Mocker, expect, ANY, MATCH
from nose.plugins.skip import SkipTest
from nose.tools import eq_, assert_raises
from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt.util import KVOList
from editxt.test.util import TestConfig

log = logging.getLogger(__name__)

def test_create_kvolist():
    lst = KVOList.alloc().init()
    eq_(len(lst.items()), 0)

def test_kvolist_items():
    lst = KVOList.alloc().init()
    newitems = NSMutableArray.alloc().init()
    lst.setItems_(newitems)
    eq_(lst.items(), newitems)

def test_kvolist_items():
    lst = KVOList.alloc().init()
    obj = object()
    ob2 = object()

    # test KVO methods
    yield do_kvolist_countOfItems, lst, 0
    yield do_kvolist_insertObject_inItemsAtIndex_, lst, obj, 0
    yield do_kvolist_countOfItems, lst, 1
    yield do_kvolist_objectInItemsAtIndex_, lst, obj, 0
    yield do_kvolist_replaceObjectInItemsAtIndex_withObject_, lst, ob2, 0
    yield do_kvolist_objectInItemsAtIndex_, lst, ob2, 0
    yield do_kvolist_removeObjectFromItemsAtIndex_, lst, 0
    yield do_kvolist_countOfItems, lst, 0

    # test list convenience methods
    yield do_kvolist_len, lst, 0
    yield do_kvolist_insert, lst, obj, 0
    yield do_kvolist_len, lst, 1
    yield do_kvolist_getitem, lst, obj, 0
    yield do_kvolist_setitem, lst, ob2, 0
    yield do_kvolist_append, lst, obj
    yield do_kvolist_delitem, lst, 1
    yield do_kvolist_contains, lst, ob2
    yield do_kvolist_not_contains, lst, obj
    yield do_kvolist_count, lst, obj, 0
    yield do_kvolist_count, lst, ob2, 1
    yield do_kvolist_extend, lst, [object(), object()]
    eq_(len(lst), 3)
    yield do_kvolist_index, lst, ob2, 0
    yield do_kvolist_iter, lst
    yield do_kvolist_remove, lst, ob2
    yield do_kvolist_remove_nonexistent, lst, obj
    yield do_kvolist_pop, lst, 1
    yield do_kvolist_pop, lst

    lst.setItems_([1, 2, 3, 4])
    yield do_kvolist_getslice, lst, 1, 3, [2, 3]

    lst.setItems_([1, 2, 3, 4])
    yield do_kvolist_setslice, lst, 1, 3, [5, 6], [1, 5, 6, 4]

    lst.setItems_([1, 2, 3, 4])
    yield do_kvolist_delslice, lst, 1, 3, [1, 4]

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
    assert lst[-1] is obj

def do_kvolist_extend(lst, objs):
    offset = len(lst)
    lst.extend(objs)
    for i in xrange(len(objs)):
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
    assert item is popped
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# recent items queue tests
from editxt.util import RecentItemStack

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
    items = range(10)
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# context map tests
from editxt.util import ContextMap

def test_create_context_map():
    map = ContextMap()
    eq_(len(map), 0)

def test_context_map_put_and_pop():
    map = ContextMap()
    obj = object()
    key = map.put(obj)
    assert isinstance(key, (int, long))
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from editxt.util import fetch_icon, load_image, filestat, user_path

def test_fetch_icon_data():
    from os.path import abspath, dirname, join
    root = dirname(dirname(abspath(__file__)))
    for args in (
        (None, False),
        ("/some/path/that/does/not/exist.txt", False),
        (join(root, "../resources/template.txt"), True),
    ):
        yield do_fetch_icon, args

def do_fetch_icon((path, exists)):
    if path is not None:
        path = os.path.abspath(path)
        if exists:
            assert os.path.exists(path), "path does not exist (but should): %s" % path
        else:
            assert not os.path.exists(path), "path exists (and should not): %s" % path
    data = fetch_icon(path)
    assert data is not None

def test_load_image():
    img = load_image("close-hover.png")
    assert isinstance(img, NSImage)

# def loadImage(name):
#     # TODO test
#     try:
#         return images[name]
#     except KeyError:
#         path = NSBundle.mainBundle().pathForImageResource_(name)
#         log.debug("loading image: %s", path)
#         url = NSURL.fileURLWithPath_(path)
#         image = NSImage.alloc().initWithContentsOfURL_(url)
#         images[name] = image
#         return image

def test_filestat():
    from editxt.util import filestat
    def test(f_exists):
        m = Mocker()
        exists = m.replace("os.path.exists")
        stat = m.replace("os.stat")
        path = "<path>"
        exists(path) >> f_exists
        if f_exists:
            stat(path) >> (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
            res = (6, 8)
        else:
            res = None
        with m:
            result = filestat(path)
            eq_(result, res)
    yield test, True
    yield test, False

def test_user_path():
    home = os.path.expanduser('~')
    if not os.getenv('HOME'):
        raise SkipTest("os.getenv('HOME') -> %r" % os.getenv('HOME'))
    def test(input, output):
        eq_(user_path(input), output)
    yield test, '%s-not/file.txt' % home, '%s-not/file.txt' % home
    yield test, '%s/file.txt' % home, '~/file.txt'
    yield test, '%s/../%s/file' % (home, os.path.basename(home)), '~/file'

def test_Invoker_invoke():
    from editxt.util import Invoker
    called = []
    def callback():
        called.append(1)
    inv = Invoker.alloc().init(callback)
    Invoker.invoke_(inv)
    eq_(called, [1])
    Invoker.invoke_(inv)
    eq_(called, [1, 1])

def test_register_undo():
    from editxt.util import Invoker, register_undo_callback
    m = Mocker()
    inv_class = m.replace(Invoker)
    cb = m.mock()
    und = m.mock(NSUndoManager)
    inv = inv_class.alloc().init(cb) >> m.mock(Invoker)
    und.registerUndoWithTarget_selector_object_(inv_class, "invoke:", inv)
    with m:
        register_undo_callback(und, cb)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from editxt.util import KVOProxy, KVOLink

_test_KVOProxy_has_run = False

def test_KVOProxy():
    KVOProxy(Mocker().mock()) # cache the proxy class to avoid side affects
    def run(test):
        m = Mocker()
        target = m.mock()
        proxy = KVOProxy(target)
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
    yield run, test_get_missing
    yield run, test_set_missing
    yield run, test_get
    yield run, test_set
    yield run, test_set_matching

def test_KVOLink():
    from editxt.util import KVOLink
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
            link = KVOLink(links)
            link.close()
    c = TestConfig()
    yield test, c(lks=[])
    yield test, c(lks=[("path.to.key", "other_key")])
    yield test, c(lks=[("path.to.key1", "other_key"), ("path.to.key2", "other_key")])

class KVOLinkItem(NSObject):
    @objc.namedSelector("init:subject:")
    def init(self, key, subj):
        super(KVOLinkItem, self).init()
        setattr(self, key, None)
        self.subj = subj
        self.proxy = KVOProxy(self)
        return self
    def _set_path(self, value):
        self.subj.key = value
    def _get_path(self):
        return self.subj.key

class KVOLinkTester(NSObject):
    was_notified = False
    def observeValueForKeyPath_ofObject_change_context_(self, path, obj, change, context):
        self.was_notified = True

def test_KVOLink_in_action():
    subj = KVOLinkItem.alloc().init("key", None)
    subj.key = "<old>"
    tester = KVOLinkTester.alloc().init()
    subj.addObserver_forKeyPath_options_context_(tester, "key", 0, 1000)
    obj = KVOLinkItem.alloc().init("path", subj)
    link = KVOLink([(obj, "path", subj, "key")])
    assert not tester.was_notified
    obj.proxy.path = "<new>"
    assert tester.was_notified
