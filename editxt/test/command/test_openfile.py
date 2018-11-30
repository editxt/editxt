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
from editxt.test.test_commands import CommandTester
from editxt.test.util import eq_, gentest, test_app

import editxt.command.openfile as mod


def test_open_command():
    @gentest
    def test(command, expected="", error=None, config="", project_path="/"):
        project_config = "({})".format(project_path) if project_path else ""
        if "*" not in config:
            project_config += "*"
        base_config = "window project{} ".format(project_config)
        with test_app(base_config + config) as app:
            editor = app.windows[0].current_editor
            CommandTester(mod.open_, editor=editor, error=error)(command)
            if not error:
                base_config = base_config.replace("*", "")
            eq_(test_app(app).state, (base_config + expected).strip())

    yield test("open file.txt", "editor[/file.txt 0]*")
    yield test("open file.txt",
               config="editor* editor",
               expected="editor editor[/file.txt 0]* editor")
    yield test("open file.txt",
               config="editor* editor(/file.txt)",
               expected="editor editor(/file.txt)*")
    yield test("open state/../file.txt",
               config="editor* editor(/file.txt)",
               expected="editor editor(/file.txt)*")
    yield test("open file.txt other.txt", "editor[/file.txt 0] editor[/other.txt 1]*")
    yield test("open", error="please specify a file path")
    yield test("open file.txt", "editor[file.txt 0]*", project_path=None)


def test_open_files():
    @gentest
    @test_app("project")
    def test(app, filepath, config, create=[]):
        tapp = test_app(app)
        for name in create:
            with open(tapp.temp_path(name), "w") as fh:
                pass
        project = app.windows[0].projects[0]
        path = tapp.temp_path(filepath)
        mod.open_files([path], project)
        eq_(tapp.state, "window project " + config)

    yield test("file.txt", "editor[/file.txt 0]*")
    yield test("file.*", "editor[/file.md 0] editor[/file.txt 1]*",
               ["filet.t", "file.md", "file.txt"])
