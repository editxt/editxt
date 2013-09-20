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
import json
import logging
from os.path import join

from editxt.test.util import eq_, TestConfig, tempdir

import editxt.history as mod

log = logging.getLogger(__name__)

def test_History__iter__():
    def test(files, lookups):
        # :param files: List of items representing history files, each
        #               being a list of commands.
        # :param lookups: List of tuples (<history index>, <command text>), ...]
        index = []
        name = "test"
        pattern = mod.History.FILENAME_PATTERN
        with tempdir() as tmp:
            for i, value in enumerate(files):
                index.append(pattern.format(name, i))
                if value is not None:
                    with open(join(tmp, pattern.format(name, i)), "wb") as fh:
                        for command in reversed(value):
                            fh.write(json.dumps(command) + "\n")
            with open(join(tmp, mod.History.INDEX_FILENAME), "wb") as fh:
                json.dump(index, fh)

            history = mod.History(tmp, 3, 5, name=name)
            eq_(list(enumerate(history)), lookups)

    yield test, [], []
    yield test, [None, None, ["command {}".format(i) for i in range(3)]], [
        (0, "command 0"),
        (1, "command 1"),
        (2, "command 2"),
    ]
    yield test, [["command {}".format(i)] for i in range(3)], [
        (0, "command 0"),
        (1, "command 1"),
        (2, "command 2"),
    ]
    yield test, \
        [["command {}".format(i + p * 3)
            for i in xrange(3)] for p in xrange(5)], \
        [(i, "command {}".format(i)) for i in xrange(15)]

def test_History_iter_matching():
    def test(name, expect, appends='abcdefghiabca'):
        with tempdir() as tmp:
            history = mod.History(tmp, 3, 5)
            for i, item in enumerate(appends):
                history.append(item + " " + str(i))

            history = mod.History(tmp, 3, 5)
            result = next(history.iter_matching(name), None)
            eq_(result, expect)

    yield test, lambda h: h.startswith("a "), "a 12"
    yield test, lambda h: h.startswith("b "), "b 10"
    yield test, lambda h: h.startswith("x "), None

def test_History_append():
    def test(appends, lookups):
        with tempdir() as tmp:
            history = mod.History(tmp, 3, 5)
            for item in appends:
                history.append(item)

            history = mod.History(tmp, 3, 5)
            eq_(list(enumerate(history)), lookups)

    yield test, [], []
    yield test, "a", [(0, "a")]
    yield test, "abac", [(0, "c"), (1, "a"), (2, "b")]
    yield test, "abcdefghiabca", [
        (0, "a"), (1, "c"), (2, "b"),
        (3, "i"), (4, "h"), (5, "g"),
        (6, "f"), (7, "e"), (8, "d"),
        (9, "c"), (10, "b"), (11, "a")
    ]
