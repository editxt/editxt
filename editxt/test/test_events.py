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

from editxt.events import eventize
from editxt.test.util import eq_

class Obj:
    class events:
        attr = eventize.attr("attr")
        child_attr = eventize.attr("child.attr")
        call = eventize.call("setup_call")
        child_call = eventize.call("child.setup_call")

    attr = None
    call = None

    def __init__(self, setup_child=True):
        eventize(self)
        if setup_child:
            self.child = Obj(setup_child=False)

    def do_attr(self):
        if self.attr is not None:
            self.attr()

    def setup_call(self, callback):
        assert self.call is None
        self.call = callback

    def do_call(self):
        if self.call is not None:
            self.call()


def test_eventize_attr():
    calls = []
    def act():
        calls.append(1)
    obj = Obj()
    obj.on.attr(act)
    eq_(sum(calls), 0)

    obj.do_attr()
    eq_(sum(calls), 1)

    calls2 = []
    def act2():
        calls2.append(1)
    obj.on.attr(act2)
    eq_(sum(calls2), 0)

    obj.do_attr()
    eq_(sum(calls), 2)
    eq_(sum(calls2), 1)


def test_eventize_attr_with_dotted_path():
    calls = []
    def act():
        calls.append(1)
    obj = Obj()
    obj.on.child_attr(act)
    eq_(sum(calls), 0)

    obj.child.do_attr()
    eq_(sum(calls), 1)

    calls2 = []
    def act2():
        calls2.append(1)
    obj.on.child_attr(act2)
    eq_(sum(calls2), 0)

    obj.child.do_attr()
    eq_(sum(calls), 2)
    eq_(sum(calls2), 1)


def test_eventize_call():
    calls = []
    def act():
        calls.append(1)
    obj = Obj()
    obj.on.call(act)
    eq_(sum(calls), 0)

    obj.do_call()
    eq_(sum(calls), 1)

    calls2 = []
    def act2():
        calls2.append(1)
    obj.on.call(act2)
    eq_(sum(calls2), 0)

    obj.do_call()
    eq_(sum(calls), 2)
    eq_(sum(calls2), 1)


def test_eventize_call_with_dotted_path():
    calls = []
    def act():
        calls.append(1)
    obj = Obj()
    obj.on.child_call(act)
    eq_(sum(calls), 0)

    obj.child.do_call()
    eq_(sum(calls), 1)

    calls2 = []
    def act2():
        calls2.append(1)
    obj.on.child_call(act2)
    eq_(sum(calls2), 0)

    obj.child.do_call()
    eq_(sum(calls), 2)
    eq_(sum(calls2), 1)
