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

# flake8: noqa: E501
import logging
import os
import re
from contextlib import contextmanager
from os.path import isabs, join

from mocker import Mocker, expect, ANY, MATCH
from nose.plugins.skip import SkipTest
from nose.tools import eq_
from editxt.test.test_commands import CommandTester
from editxt.test.util import assert_raises, gentest, TestConfig, test_app, tempdir

import editxt.command.ag as mod


def test_ag():
    if not mod.is_ag_installed():
        raise SkipTest("ag not installed")
    @gentest
    def test(command, message="", selection="", state="window project(/) editor(/dir/b.txt)*"):
        cfg = {"command.ag.options": "--workers=1"}
        with test_app(state, cfg) as app, setup_files(test_app(app).tmp) as tmp:
            editor = app.windows[0].current_editor
            if selection:
                editor.document.text_storage[:] = selection
                editor.text_view = TestConfig(selectedRange=lambda:(0, len(selection)))
            bar = CommandTester(mod.ag, editor=editor, output=True)
            bar(command)
            output = bar.output
            if output is not None:
                output = output.replace("xt://open/%s/" % tmp, "xt://open/")
                if "Traceback (most recent call last):" in output:
                    print(output)
                    assert "Traceback (most recent call last):" not in message
            eq_(output, markup(message))
            eq_(test_app(app).state, state)

    yield test("ag ([bB]|size:\\ 10)",
        "[dir/B file](xt://open/dir/B%20file)\n"
        "[1](xt://open/dir/B%20file?goto=1):name: dir/[B](xt://open/dir/B%20file?goto=1.10.1) file\n"
        "[2](xt://open/dir/B%20file?goto=2):[size: 10](xt://open/dir/B%20file?goto=2.0.8)\n"
        "\n"
        "[dir/b.txt](xt://open/dir/b.txt)\n"
        "[1](xt://open/dir/b.txt?goto=1):name: dir/[b](xt://open/dir/b.txt?goto=1.10.1).txt\n")
    yield test("ag dir/[bB] ..",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B](xt://open/dir/../dir/B%20file?goto=1.6.5) file\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: [dir/b](xt://open/dir/../dir/b.txt?goto=1.6.5).txt\n")
    yield test("ag dir/[bB] .. --after=1",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B](xt://open/dir/../dir/B%20file?goto=1.6.5) file\n"
        "[2](xt://open/dir/../dir/B%20file?goto=2):size: 10\n\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: [dir/b](xt://open/dir/../dir/b.txt?goto=1.6.5).txt\n"
        "[2](xt://open/dir/../dir/b.txt?goto=2):size: 9\n\n")
    yield test("ag dir/b .. -i",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B](xt://open/dir/../dir/B%20file?goto=1.6.5) file\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: [dir/b](xt://open/dir/../dir/b.txt?goto=1.6.5).txt\n")
    yield test("ag  ..",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B ](xt://open/dir/../dir/B%20file?goto=1.6.6)file\n",
        selection="dir/B ")
    yield test("ag xyz", "no match for pattern: xyz")
    yield test("ag txt",
        "[dir/a.txt](xt://open/dir/a.txt)\n"
        "[1](xt://open/dir/a.txt?goto=1):name: dir/a.[txt](xt://open/dir/a.txt?goto=1.12.3)\n"
        "\n"
        "[dir/b.txt](xt://open/dir/b.txt)\n"
        "[1](xt://open/dir/b.txt?goto=1):name: dir/b.[txt](xt://open/dir/b.txt?goto=1.12.3)\n"
        "\n"
        "[e.txt](xt://open/e.txt)\n"
        "[1](xt://open/e.txt?goto=1):name: e.[txt](xt://open/e.txt?goto=1.8.3)\n")
    yield test("ag txt .",
        "[a.txt](xt://open/dir/./a.txt)\n"
        "[1](xt://open/dir/./a.txt?goto=1):name: dir/a.[txt](xt://open/dir/./a.txt?goto=1.12.3)\n"
        "\n"
        "[b.txt](xt://open/dir/./b.txt)\n"
        "[1](xt://open/dir/./b.txt?goto=1):name: dir/b.[txt](xt://open/dir/./b.txt?goto=1.12.3)\n")
    yield test("ag txt ..",
        "[dir/a.txt](xt://open/dir/../dir/a.txt)\n"
        "[1](xt://open/dir/../dir/a.txt?goto=1):name: dir/a.[txt](xt://open/dir/../dir/a.txt?goto=1.12.3)\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: dir/b.[txt](xt://open/dir/../dir/b.txt?goto=1.12.3)\n"
        "\n"
        "[e.txt](xt://open/dir/../e.txt)\n"
        "[1](xt://open/dir/../e.txt?goto=1):name: e.[txt](xt://open/dir/../e.txt?goto=1.8.3)\n")
    yield test("ag txt ...",
        "[dir/a.txt](xt://open/dir/a.txt)\n"
        "[1](xt://open/dir/a.txt?goto=1):name: dir/a.[txt](xt://open/dir/a.txt?goto=1.12.3)\n"
        "\n"
        "[dir/b.txt](xt://open/dir/b.txt)\n"
        "[1](xt://open/dir/b.txt?goto=1):name: dir/b.[txt](xt://open/dir/b.txt?goto=1.12.3)\n"
        "\n"
        "[e.txt](xt://open/e.txt)\n"
        "[1](xt://open/e.txt?goto=1):name: e.[txt](xt://open/e.txt?goto=1.8.3)\n")
    yield test("ag txt",
        "[a.txt](xt://open/dir/a.txt)\n"
        "[1](xt://open/dir/a.txt?goto=1):name: dir/a.[txt](xt://open/dir/a.txt?goto=1.12.3)\n"
        "\n"
        "[b.txt](xt://open/dir/b.txt)\n"
        "[1](xt://open/dir/b.txt?goto=1):name: dir/b.[txt](xt://open/dir/b.txt?goto=1.12.3)\n",
        state="window project editor(/dir/b.txt)*")
    yield test("ag xyz", "please specify a search path", state="window project editor*")


def test_exec_shell():
    if not mod.is_ag_installed():
        raise SkipTest("ag not installed")
    with setup_files() as tmp:
        result = mod.exec_shell(["ag", "dir/[bB]", "--workers=1"], cwd=tmp)

        eq_(result, 'dir/B file:1:name: dir/B file\n'
                    'dir/b.txt:1:name: dir/b.txt\n')
        eq_(result.err, None)
        eq_(result.returncode, 0)


@contextmanager
def setup_files(tmp=None):
    def do_setup(tmp):
        os.mkdir(join(tmp, "dir"))
        for path in [
            "dir/a.txt",
            "dir/b.txt",
            "dir/B file",
            "e.txt",
        ]:
            assert not isabs(path), path
            with open(join(tmp, path), "w") as fh:
                fh.write("name: {}\nsize: {}".format(path, len(path)))
        assert " " not in tmp, tmp

    if tmp is None:
        with tempdir() as tmp:
            do_setup(tmp)
            yield tmp
    else:
        do_setup(tmp)
        yield tmp


def markup(text, link=re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")):
    return link.subn(r"<a href='\2'>\1</a>", text)[0].replace("\n", "<br />")
