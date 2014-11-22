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
import re
from functools import partial

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_
from editxt.test.command import FakeTextView
from editxt.test.test_commands import CommandTester
from editxt.test.util import assert_raises, gentest, TestConfig, test_app

import editxt.command.openfile as mod


def test_open_command():
    @gentest
    def test(command, expected="", error=None, config="", project_path="/"):
        project_config = "({})".format(project_path) if project_path else ""
        base_config = "window project{} ".format(project_config)
        with test_app(base_config + config) as app:
            tapp = test_app(app)
            view = FakeTextView("")
            view.editor = FakeEditor(app.windows[0].projects[0])
            CommandTester(mod.open_, textview=view, error=error)(command)
            eq_(tapp.state, (base_config + expected).strip())

    yield test("open file.txt", "editor[/file.txt 0]*")
    yield test("open file.txt",
               config="editor* editor",
               expected="editor editor[/file.txt 0]* editor")
    yield test("open file.txt other.txt", "editor[/file.txt 0] editor[/other.txt 1]*")
    yield test("open", error="please specify a file path")
    yield test("open file.txt", "editor[~/file.txt 0]*", project_path=None)

def test_open_files():
    with test_app("project") as app:
        tapp = test_app(app)
        project = app.windows[0].projects[0]
        path = tapp.temp_path("file.txt")
        mod.open_files([path], project)
        eq_(tapp.state, "window project editor[/file.txt 0]*")


class FakeEditor(object):

    def __init__(self, project):
        self.project = project

    def dirname(self):
        return self.project.dirname()
