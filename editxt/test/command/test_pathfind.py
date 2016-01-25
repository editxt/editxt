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
import os
from functools import partial
from os.path import isabs, join

from mocker import Mocker, expect, ANY, MATCH
from editxt.test.util import eq_, gentest, test_app

import editxt.command.pathfind as mod
from editxt.test.test_commands import CommandTester


def test_pathfind_title():
    eq_(mod.pathfind.title, "Find file by path")


def test_pathfind():
    filesystem = [
        "dir/a_file.txt",
        "dir/file.txt",
        "dir/file_b.txt",
        "dir/file/txt",
        "file.doc",
        "file.txt",
    ]
    initial_config = "window project(/dir) editor*"

    @gentest
    @test_app(initial_config)
    def test(app, command, files=None, config="", selection=(0, 0)):
        tmp = test_app(app).tmp
        os.mkdir(join(tmp, "dir"))
        os.mkdir(join(tmp, "dir", "file"))
        for path in filesystem:
            assert not isabs(path), path
            with open(join(tmp, path), "w") as fh:
                pass

        if command:
            parts = command.split(' ')
            if len(parts) > 2:
                if parts[2].startswith("/"):
                    parts[2] = join(tmp, parts[2].lstrip("/"))
            assert all(p.startswith(tmp + "/")
                       for p in parts if p.startswith("/")), parts
            command = " ".join(parts)
            print(command)

        editor = app.windows[0].current_editor
        if editor.document is not None:
            editor.document.text_storage[:] = "from file.txt import txt"
        m = Mocker()
        view = editor.text_view = m.mock()
        (view.selectedRange() << selection).count(0, 4)
        with m:
            bar = CommandTester(mod.pathfind, editor=editor, output=True)
            bar(command)
        output = bar.output
        if files is None:
            assert output is None, output
        else:
            if output is not None:
                output = output.replace(tmp + "/", "/")
            message = "\n".join("[{}](xt://open/{}{})".format(
                f[0] if isinstance(f, tuple) else f,
                f[1] if isinstance(f, tuple) else "/dir/",
                (f[0] if isinstance(f, tuple) else f).replace(".../", "")
            ) for f in files)
            eq_(output, message)
        if config:
            tapp = test_app(app)
            eq_(tapp.state, tapp.config.replace("*", "") + config)

    file_txt = [".../a_file.txt", ".../file.txt", ".../file/txt"]

    # simulate invoke with hotkey
    yield test(None, file_txt, selection=(5, 8))

    yield test("pathfind", file_txt, selection=(5, 8))

    base_test = test
    for cfg in [None, "window project(/dir)* editor"]:
        test = base_test if cfg is None else partial(base_test, app_config=cfg)
        yield test("pathfind file\.txt", [".../a_file.txt", ".../file.txt"])
        yield test("pathfind file.txt", file_txt)
        yield test("pathfind file\.txt /", [
            ("/file.txt", ""),
            ".../a_file.txt",
            ".../file.txt",
        ])
        yield test("pathfind a_file", config=" editor[/dir/a_file.txt 0]*")
        yield test("pathfind a_file  disp", [".../a_file.txt"])
        yield test("pathfind a_file  first", config=" editor[/dir/a_file.txt 0]*")
