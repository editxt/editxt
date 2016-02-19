# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH

import editxt.undo as mod
from editxt.test.util import assert_raises, eq_, TestConfig, replattr, test_app, make_file

def test_UndoManager_has_unsaved_actions():
    seen = set()
    dups = []
    def test(actions, result, state):
        if actions in seen:
            dups.append(actions)
        seen.add(actions)

        undo, stack = simulate(actions)
        eq_(stack.state, state)
        eq_(undo.has_unsaved_actions(), result)

    yield test, "", False, []
    yield test, "1", True, [1]
    yield test, "1s", False, [1]
    yield test, "1su", True, []
    yield test, "1u", False, []
    yield test, "1uru", False, []

    yield test, "11s", False, [1, 1]
    yield test, "11su", True, []
    yield test, "11sur", False, [1, 1]
    yield test, "11su1", True, [1]
    yield test, "11su1ur", True, [1]
    yield test, "11s1u", False, [1, 1]
    yield test, "11s1ur", True, [1, 1, 1]

    yield test, "12s", False, [1, 2]
    yield test, "12su", True, [1]
    yield test, "12sur", False, [1, 2]
    yield test, "12su1", True, [1, 1]
    yield test, "12su1ur", True, [1, 1]
    yield test, "12su11ur", True, [1, 1, 1]
    yield test, "12su12ur", True, [1, 1, 2]

    yield test, "1se", False, [1] # WARNING unbalanced endUndoGrouping
    yield test, "1sbee", False, [1] # WARNING unbalanced endUndoGrouping
    yield test, "1sb1eu", False, [1]
    yield test, "1sb1eu1", True, [1, 1]
    yield test, "1sb1euu", True, []
    yield test, "1sb1eur", True, [1, 1]
    yield test, "1sb1eus", False, [1]
    yield test, "1sb1eurs", False, [1, 1]
    yield test, "1sb1eurs1", True, [1, 1, 1]

    yield test, "1ssu", True, []
    yield test, "1ssur", False, [1]
    yield test, "1ssu1", True, [1]
    yield test, "1ssur1", True, [1, 1]

    yield test, "1susr", True, [1]
    yield test, "1susrs", False, [1]
    yield test, "1b1esu", True, []
    yield test, "1b1esusr", True, [1, 1]
    yield test, "1b1esusrs", False, [1, 1]

    assert not dups, "duplicate tests: %r" % dups

def test_UndoManager_has_unsaved_actions_changed_callbacks():
    def make_callback():
        calls = []
        def callback(value):
            calls.append(value)
        def callstr():
            return "".join(str(v)[0].lower() for v in calls)
        callback.callstr = callstr
        return callback

    def test(actions, changes, state):
        cb1 = make_callback()
        cb2 = make_callback()
        cb3 = make_callback()
        undo = mod.UndoManager()
        undo.on(cb1)
        undo.on(cb2)
        undo.on(cb3)
        cb3_callstr = cb3.callstr
        undo.off(cb3)
        undo, stack = simulate(actions, undo)
        eq_(cb1.callstr(), changes)
        eq_(cb2.callstr(), changes)
        eq_(cb3_callstr(), "")
        eq_(stack.state, state)
        eq_(undo.has_unsaved_actions(), (changes[-1] == "t" if changes else False))

    yield test, "1", "t", [1]
    yield test, "11", "t", [1, 1]
    yield test, "12", "t", [1, 2]
    yield test, "12u", "t", [1]
    yield test, "12uu", "tf", []
    yield test, "12us", "tf", [1]
    yield test, "12uur", "tft", [1]
    yield test, "12su1", "tft", [1, 1]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# test helpers

def simulate(actions, undo=None):
    """Undo simulator

    action key
    1 - plain edit
    2 - end+begin undo grouping and edit
    s - save
    u - undo
    r - redo
    b - begin undo grouping
    e - end undo grouping
    """
    if undo is None:
        undo = mod.UndoManager()
    stack = Stack.alloc().init_(undo)
    for action in actions:
        if action == "1":
            stack.push_(1)
        elif action == "2":
            undo.endUndoGrouping()
            undo.beginUndoGrouping()
            stack.push_(2)
        elif action == "s":
            undo.savepoint()
            print("savepoint")
        elif action == "b":
            undo.beginUndoGrouping()
        elif action == "e":
            undo.endUndoGrouping()
        elif action == "u":
            print("undo")
            undo.undo()
        else:
            print("redo")
            eq_(action, "r")
            undo.redo()
    print("has unsaved actions:", undo.has_unsaved_actions())
    return undo, stack


class Stack(fn.NSObject):

    def init_(self, undo):
        self.undo = undo
        self.state = []
        return self

    def push_(self, value):
        self.undo.prepareWithInvocationTarget_(self).pop()
        self.undo.setActionName_("Push")
        self.state.append(value)
        print("push", self.state, "level=%s" % self.undo.groupingLevel())

    def pop(self):
        value = self.state.pop()
        self.undo.registerUndoWithTarget_selector_object_(self, b"push:", value)
        self.undo.setActionName_("Pop")
        print("pop ", self.state, "level=%s" % self.undo.groupingLevel())
        return value
