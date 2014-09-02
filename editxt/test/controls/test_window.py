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
import os

from mocker import Mocker, expect, ANY
from nose.tools import eq_
from editxt.test.util import TestConfig

from editxt.controls.window import EditorWindow

def test_EditorWindow_add_mouse_moved_responder():
    window = EditorWindow.alloc().init()
    obj = object()
    eq_(window.mouse_moved_responders, set())
    window.add_mouse_moved_responder(obj)
    eq_(window.mouse_moved_responders, set([obj]))
    window.add_mouse_moved_responder(obj)
    eq_(window.mouse_moved_responders, set([obj]))

def test_EditorWindow_remove_mouse_moved_responder():
    window = EditorWindow.alloc().init()
    obj1 = object()
    obj2 = object()
    eq_(window.mouse_moved_responders, set())
    window.remove_mouse_moved_responder(obj1)
    window.add_mouse_moved_responder(obj1)
    window.add_mouse_moved_responder(obj2)
    eq_(window.mouse_moved_responders, set([obj1, obj2]))
    window.remove_mouse_moved_responder(obj1)
    eq_(window.mouse_moved_responders, set([obj2]))
    window.remove_mouse_moved_responder(obj2)
    window.remove_mouse_moved_responder(obj2) # second remove should not err
    eq_(window.mouse_moved_responders, set())

def test_EditorWindow_accepts_mouse_move_events():
    window = EditorWindow.alloc().init()
    obj1 = object()
    obj2 = object()
    eq_(window.acceptsMouseMovedEvents(), False)
    window.add_mouse_moved_responder(obj1)
    eq_(window.acceptsMouseMovedEvents(), True)
    window.add_mouse_moved_responder(obj2)
    eq_(window.acceptsMouseMovedEvents(), True)
    window.remove_mouse_moved_responder(obj1)
    eq_(window.acceptsMouseMovedEvents(), True)
    window.remove_mouse_moved_responder(obj2)
    eq_(window.acceptsMouseMovedEvents(), False)
