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
import shlex
from os.path import basename, exists, join
from subprocess import check_call
from tempfile import gettempdir

from mocker import Mocker, expect, ANY, MATCH
from editxt.test.util import (assert_raises, eq_, TestConfig, replattr,
    tempdir, test_app)

import editxt.command.diff as mod
from editxt.platform.views import TextView

log = logging.getLogger(__name__)


def test_diff_title():
    eq_(mod.diff.title, "Diff with original")


def test_diff():
    def test(original):
        diffed = []
        def diff_stub(filepath, text, name, diff_program):
            eq_(filepath, path)
            eq_(text, "def")
            eq_(name, "file.txt")
            eq_(diff_program, "opendiff")
            diffed.append(1)
        with tempdir() as tmp, test_app("editor") as app, \
                replattr(mod, "external_diff", diff_stub):
            editor = app.windows[0].projects[0].editors[0]
            path = editor.file_path = join(tmp, "file.txt")
            with open(path, mode="w", encoding="utf8") as fh:
                fh.write("abc")
            if original:
                args = None
            else:
                path = join(tmp, "other.txt")
                with open(path, mode="w", encoding="utf8") as fh:
                    fh.write("other")
                assert " " not in path, path
                args = mod.diff.arg_parser.parse(path)
            m = Mocker()
            text_view = editor.text_view = m.mock(TextView)
            text_view.string() >> "def"
            with m:
                mod.diff(editor, args)
                assert diffed
    yield test, True
    yield test, False

def test_diff_missing_file():
    def test(msg, has_path=False):
        with test_app("editor") as app:
            editor = app.windows[0].projects[0].editors[0]
            if has_path:
                path = editor.file_path = "/file-that-does-not-exist.not"
                msg = msg.format(path)
            if editor.file_path and os.path.exists(editor.file_path):
                raise RuntimeError("cannot run test because file exists: {}"
                    .format(editor.file_path))
            msg.format(editor.file_path)
            m = Mocker()
            with m, assert_raises(mod.CommandError, msg=msg):
                mod.diff(editor, None)
    yield test, "file has not been saved"
    yield test, "file not found: {}", True

def test_external_diff():
    popen_called = []
    def popen(command, **kw):
        popen_called.append(True)
        print(command)
        file2 = None
        try:
            eq_(sum(1 for c in command if c == ";"), 1, command)
            args = shlex.split(command.split(";")[0])
            print(args)
            eq_(args[:2], [":", "-d"])
            file1 = args[2]
            file2 = args[3]
            assert basename(file2).startswith("file-"), file2
            assert basename(file2).endswith(".txt"), file2
            assert exists(file2), file2
            check_call(command, **kw)
            assert not exists(file2), "test file not removed: {}".format(file2)
        finally:
            if file2 is not None and exists(file2):
                os.remove(file2)
    with tempdir() as tmp, replattr(mod, "Popen", popen):
        path = join(tmp, "file.txt")
        with open(path, mode="w") as fh:
            fh.write("abc")
        mod.external_diff(path, "def", "file.txt", ": -d")
        assert popen_called, "diff command was not executed"
