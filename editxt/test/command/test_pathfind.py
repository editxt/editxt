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

from mocker import Mocker
from nose.plugins.skip import SkipTest
from editxt.test.util import eq_, gentest, test_app

import editxt.command.pathfind as mod
import editxt.config as config
from editxt.command.ag import is_ag_installed
from editxt.test.test_commands import CommandTester


def test_pathfind_title():
    eq_(mod.pathfind.title, "Find file by path")


def test_pathfind():
    if not is_ag_installed():
        raise SkipTest("ag not installed")

    filesystem = [
        ".git/file.txt",  # excluded by default
        "dir/a_file.txt",
        "dir/file.pyc",
        "dir/file.txt",
        "dir/file_b.txt",
        "dir/file/txt",
        "file.doc",
        "file.txt",
    ]

    @gentest
    @test_app("window project(/dir) editor*")
    def test(app, command, files=None, selection=(0, 0)):
        app.config.extend("ag", {
            "path": config.String("ag"),
            "options": config.String(""),
        })
        tmp = test_app(app).tmp
        os.mkdir(join(tmp, ".git"))
        os.mkdir(join(tmp, "dir"))
        os.mkdir(join(tmp, "dir", "file"))
        for path in filesystem:
            assert not isabs(path), path
            with open(join(tmp, path), "w") as fh:
                fh.write(" ")
        with open(join(tmp, ".gitignore"), "w") as fh:
            fh.write("*.pyc\n")

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
            expect = " ".join("<a href='xt://open/{0}{1}'>{1}</a>".format(
                "/" if f.startswith("/") else "/dir/",
                f[1:] if f.startswith("/") else f,
            ) for f in files)
            eq_(" ".join(sorted(x for x in output.split("<br />") if x)), expect)

    file_txt = ["a_file.txt", "file.txt", "file/txt"]

    # simulate invoke with hotkey
    yield test(None, file_txt, selection=(5, 8))

    yield test("pathfind", file_txt, selection=(5, 8))

    base_test = test
    for cfg in [None, "window project(/dir)* editor"]:
        test = base_test if cfg is None else partial(base_test, init_state=cfg)
        yield test("pathfind file.txt", file_txt)
        yield test("pathfind file\\.txt", ["a_file.txt", "file.txt"])
        yield test("pathfind file\\. /", [
            "/dir/a_file.txt",
            "/dir/file.txt",
            "/file.doc",
            "/file.txt",
        ])
        yield test("pathfind file\\. / unrestricted", [
            "/.git/file.txt",
            "/dir/a_file.txt",
            "/dir/file.pyc",
            "/dir/file.txt",
            "/file.doc",
            "/file.txt",
        ])
