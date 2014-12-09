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
import logging
import os
from contextlib import contextmanager
from os.path import isabs, join

from mocker import Mocker, expect, ANY, MATCH
from nose.plugins.skip import SkipTest
from nose.tools import eq_
from editxt.test.test_commands import CommandTester
from editxt.test.util import assert_raises, gentest, TestConfig, test_app, tempdir

import editxt.command.ack as mod


def test_ack():
    if not mod.is_ack_installed():
        raise SkipTest("ack not installed")
    @gentest
    def test(command, message="", config="", project_path="/"):
        config = "window project(/) editor(/dir/b.txt)*"
        with test_app(config) as app, \
                setup_files(test_app(app).tmp) as tmp:
            editor = app.windows[0].current_editor
            bar = CommandTester(mod.ack, editor=editor, output=True)
            bar(command)
            output = bar.output
            if output is not None:
                output = output.replace("xt://open/%s/" % tmp, "xt://open/")
            eq_(output, message)
            eq_(test_app(app).state, config)

    yield test("ack ([bB]|size:\ 10)",
        "[B file](xt://open/dir/B%20file)\n"
        "[1](xt://open/dir/B%20file?goto=1):name: dir/[B](xt://open/dir/B%20file?goto=1.10.1) file\n"
        "[2](xt://open/dir/B%20file?goto=2):[size: 10](xt://open/dir/B%20file?goto=2.0.8)\n"
        "\n"
        "[b.txt](xt://open/dir/b.txt)\n"
        "[1](xt://open/dir/b.txt?goto=1):name: dir/[b](xt://open/dir/b.txt?goto=1.10.1).txt\n")
    yield test("ack dir/[bB] ..",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B](xt://open/dir/../dir/B%20file?goto=1.6.5) file\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: [dir/b](xt://open/dir/../dir/b.txt?goto=1.6.5).txt\n")
    yield test("ack dir/[bB] .. --after=1",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B](xt://open/dir/../dir/B%20file?goto=1.6.5) file\n"
        "[2](xt://open/dir/../dir/B%20file?goto=2)-size: 10\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: [dir/b](xt://open/dir/../dir/b.txt?goto=1.6.5).txt\n"
        "[2](xt://open/dir/../dir/b.txt?goto=2)-size: 9\n")
    yield test("ack dir/b .. -i",
        "[dir/B file](xt://open/dir/../dir/B%20file)\n"
        "[1](xt://open/dir/../dir/B%20file?goto=1):name: [dir/B](xt://open/dir/../dir/B%20file?goto=1.6.5) file\n"
        "\n"
        "[dir/b.txt](xt://open/dir/../dir/b.txt)\n"
        "[1](xt://open/dir/../dir/b.txt?goto=1):name: [dir/b](xt://open/dir/../dir/b.txt?goto=1.6.5).txt\n")
    yield test("ack xyz", None)

def test_exec_shell():
    if not mod.is_ack_installed():
        raise SkipTest("ack not installed")
    with setup_files() as tmp:
        result = mod.exec_shell(["ack", "dir/[bB]"], cwd=tmp)

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
