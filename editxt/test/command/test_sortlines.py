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

from mocker import Mocker, ANY
from testil import eq_
from editxt.test.util import TestConfig, test_app

import editxt.command.base as base
import editxt.command.sortlines as mod
from editxt.command.sortlines import SortLinesController, SortOptions, sortlines
from editxt.command.parser import RegexPattern
from editxt.platform.text import Text
from editxt.test.test_commands import CommandTester

log = logging.getLogger(__name__)

TEXT = """
ghi 1 2 012
abc 3 1 543
 de 2 1 945
Jkl 4 1 246
    
"""


def test_sort_command():
    def test(command, expected):
        m = Mocker()
        do = CommandTester(mod.sort_lines, text=TEXT, sel=(0, 0))
        with m:
            do(command)
            eq_(sort_result(do.editor.text), expected, TEXT)

    yield test, "sort", "|0gadJ|4|0"
    yield test, "sort all", "|0|4dagJ|0"
    yield test, "sort all   match-case", "|0|4dJag|0"


def test_SortLinesController_default_options():
    with test_app() as app:
        editor = base.Options(app=app)
        ctl = SortLinesController(editor)
        for name, value in SortOptions.DEFAULTS.items():
            eq_(getattr(ctl.options, name), value, name)


def test_SortLinesController_load_options():
    def test(hist, opts):
        with test_app() as app:
            editor = base.Options(app=app)
            app.text_commander.history.append(hist)
            ctl = SortLinesController(editor)
            eq_(ctl.options._target, SortOptions(**opts))

    yield test, "sort", {}
    yield test, "sort all", {"selection": False}
    yield test, "sort  rev ignore-leading ignore-case /(\d+)([a-z]+)/\2\1/i", {
        "reverse": True,
        "ignore_leading_whitespace": True,
        "ignore_case": True,
        "search_pattern": RegexPattern("(\d+)([a-z]+)"),
        "match_pattern": "\2\1",
    }
    yield test, "sort /(\d+)([a-z]+)/\2\1/i", {
        "search_pattern": RegexPattern("(\d+)([a-z]+)"),
        "match_pattern": "\2\1",
    }


def test_SortLinesController_sort_():
    m = Mocker()
    sort = m.replace(mod, 'sortlines')
    with test_app() as app:
        editor = base.Options(app=app)
        slc = SortLinesController(editor)
        sort(editor, slc.options)
        m.method(slc.save_options)()
        m.method(slc.cancel_)(None)
        with m:
            slc.sort_(None)


def test_sortlines():
    optmap = [
        ("sel", "selection"),
        ("rev", "reverse"),
        ("ign", "ignore_leading_whitespace"),
        ("icase", "ignore_case"),
        ("num", "numeric_match"),
        ("reg", "regex_sort"),
        ("sch", "search_pattern"),
        ("mch", "match_pattern"),
    ]
    def test(c):
        opts = SortOptions(**{opt: c.opts[abbr]
            for abbr, opt in optmap if abbr in c.opts})
        m = Mocker()
        editor = m.mock()
        text = editor.text >> Text(c.text)
        if opts.selection:
            sel = editor.selection >> c.sel
            sel = text.line_range(sel)
        else:
            sel = c.sel
        output = []

        def put(text, range, select=False):
            output.append(text)
        (editor.put(ANY, sel, select=opts.selection) << True).call(put)
        with m:
            sortlines(editor, opts)
            eq_(sort_result(output[0]), c.result, output[0])
    op = TestConfig()
    tlen = len(TEXT)
    c = TestConfig(text=TEXT, sel=(0, tlen), opts=op)
    yield test, c(result="|0|4dagJ|0")
    yield test, c(result="|0|4adgJ|0", opts=op(ign=True))
    yield test, c(result="|0|4dJag|0", opts=op(icase=False))
    yield test, c(result="|0|4Jadg|0", opts=op(icase=False, ign=True))
    yield test, c(result="dag|0", opts=op(sel=True), sel=(5, 32))
    yield test, c(result="adg|0", opts=op(sel=True, ign=True), sel=(5, 32))
    yield test, c(result="Jgad|4|0|0", opts=op(rev=True))
    
    op = op(reg=True, sch=r"\d")
    yield test, c(result="|0|4dagJ|0", opts=op(reg=False))
    yield test, c(result="gdaJ|0|4|0", opts=op)
    yield test, c(result="daJg|0|4|0", opts=op(sch=r"(\d) (\d)", mch=r"\2\1"))
    # TODO test and implement numeric match (checkbox is currently hidden)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# test helpers

def sort_result(value):
    def ch(line):
        val = line.lstrip(" ")
        return val[0] if val else "|%i" % len(line)
    return "".join(ch(line) for line in str(value).split("\n"))
