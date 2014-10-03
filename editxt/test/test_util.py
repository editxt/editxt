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
import logging
import os

import objc
from mocker import Mocker, expect, ANY, MATCH
from nose.plugins.skip import SkipTest
import AppKit as ak
import Foundation as fn

import editxt.constants as const
import editxt.util as mod
from editxt.test.util import (assert_raises, eq_, gentest, make_file, tempdir,
    TestConfig)

log = logging.getLogger(__name__)

def test_atomicfile():
    def test(expect, old_value=None):
        if isinstance(expect, Exception):
            exc = type(expect)
            exc_val = expect
        elif expect == old_value:
            exc = IOError
            exc_val = IOError("fail")
        else:
            exc = exc_val = None
        with tempdir() as tmp:
            path = os.path.join(tmp, "file.txt")
            if old_value is not None:
                with open(path, "x") as fh:
                    fh.write(old_value)
            with assert_raises(exc, msg=exc_val):
                with mod.atomicfile(path) as fh:
                    fh.write("new")
                    if exc_val is not None:
                        raise exc_val
            files = os.listdir(tmp)
            if exc is None:
                with open(path) as fh:
                    eq_(fh.read(), expect)
                assert files == ["file.txt"], files
            elif old_value is not None:
                assert files == ["file.txt"], files
                with open(path) as fh:
                    eq_(fh.read(), old_value)
            else:
                assert not files, files
    yield test, "new"
    yield test, "new", "old"
    yield test, "old", "old"
    yield test, KeyError("fail!")
    yield test, KeyError("fail!"), "old"

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

def do_fetch_icon(path_exists):
    (path, exists) = path_exists
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
    assert isinstance(img, ak.NSImage)

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
        with make_file() as path:
            if f_exists:
                stat = os.stat(path)
                res = (stat.st_size, stat.st_mtime)
            else:
                path += "-not-found"
                res = None
            eq_(filestat(path), res)
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
    from editxt.util import register_undo_callback
    m = Mocker()
    inv_class = m.replace(mod, 'Invoker')
    cb = m.mock()
    und = m.mock(fn.NSUndoManager)
    inv = inv_class.alloc().init(cb) >> m.mock(mod.Invoker)
    und.registerUndoWithTarget_selector_object_(inv_class, "invoke:", inv)
    with m:
        register_undo_callback(und, cb)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# editxt.test.util tests
from editxt.test.util import test_app


def test_gentest():
    class Args(object):
        def __init__(self, *args, **kw):
            self.args = args
            self.kw = kw
        def __repr__(self):
            return "%s %s" % (self.args, self.kw)
    def test(args, rep, result):
        called = []
        @gentest
        def test(a, b=2, c=3):
            called.append((a, b, c))

        eq_(called, [])
        args = test(*args.args, **args.kw)
        run, args = args[0], args[1:]
        eq_(called, [])
        eq_(repr(args), rep)
        run(*args)
        eq_(called, [result])

    yield test, Args(1), "(1,)", (1, 2, 3)
    yield test, Args(1, c=0), "(1, c=0)", (1, 2, 0)
    yield test, Args(a=2, b=4), "(a=2, b=4,)", (2, 4, 3)


def test_test_app_context_manager():
    from editxt.window import Window
    with test_app("editor(1)") as app:
        assert app is not None
        window = Window(app)
        app.windows.append(window)
    eq_(test_app(app).state, "window project editor(1) window[0]")


def test_test_app_decorator():
    from editxt.window import Window
    called = set()

    @test_app
    def test(app):
        called.add(1)
        assert app is not None
        window = Window(app)
        app.windows.append(window)
        eq_(test_app(app).state, "window[0]")
    yield test,

    @test_app("editor(2)")
    def test(app):
        called.add(2)
        assert app is not None
        window = Window(app)
        app.windows.append(window)
        eq_(test_app(app).state, "window project editor(2) window[0]")
    yield test,

    if called != {1, 2}:
        raise Exception("@test_app decorator test not executed")
