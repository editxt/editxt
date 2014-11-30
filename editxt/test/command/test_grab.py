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
from textwrap import dedent

from editxt.test.test_commands import CommandTester
from editxt.test.util import assert_raises, eq_, gentest, TestConfig, test_app

import editxt.command.grab as mod


def test_grab():
    DOC_TEXT = dedent("""
        # EditXT is free software: you can redistribute it and/or modify
        # it under the terms of the GNU General Public License as published by
        # the Free Software Foundation, either version 3 of the License, or
        # (at your option) any later version.
        #
        # EditXT is distributed in the hope that it will be useful,
        # but WITHOUT ANY WARRANTY; without even the implied warranty of
        # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        # GNU General Public License for more details.
    """).lstrip()
    @gentest
    def test(command, message=None, text=DOC_TEXT, select=None):
        with test_app("window project(/) editor*") as app:
            editor = app.windows[0].current_editor
            editor.document.text = text
            class textview:
                def selectedRange():
                    return select or (0, 0)
            editor.text_view = textview
            bar = CommandTester(mod.grab, editor=editor, output=True)
            bar(command)
            eq_(bar.output, message)

    yield test("grab EditXT", dedent("""
        # EditXT is free software: you can redistribute it and/or modify
        # EditXT is distributed in the hope that it will be useful,
        """).lstrip())
    yield test("grab /^# .?t/", dedent("""
        # it under the terms of the GNU General Public License as published by
        # the Free Software Foundation, either version 3 of the License, or
        """).lstrip())
    yield test("grab /by$/", dedent("""
        # it under the terms of the GNU General Public License as published by
        """).lstrip())
    yield test("grab the invert", dedent("""
        # EditXT is free software: you can redistribute it and/or modify
        # (at your option) any later version.
        #
        # GNU General Public License for more details.
        """).lstrip())
    yield test("grab the  selection", dedent("""
        # it under the terms of the GNU General Public License as published by
        # the Free Software Foundation, either version 3 of the License, or
        """).lstrip(), select=(17, 204))
    yield test("grab xyz")
