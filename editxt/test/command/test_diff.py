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
from os.path import basename, exists, join, splitext
from subprocess import check_call
from tempfile import gettempdir

from mocker import Mocker, expect, ANY, MATCH
from editxt.test.util import (assert_raises, eq_, make_dirty, TestConfig,
    Regex, replattr, tempdir, test_app)

import editxt.command.diff as mod
from editxt.platform.views import TextView

log = logging.getLogger(__name__)


def test_diff_title():
    eq_(mod.diff.title, "Diff with original")


def test_diff():
    def test(original, config="editor"):
        diffed = []
        text_name = "file.txt"
        rm = []
        def diff_stub(path1, path2, diff_program, remove=None):
            for path in remove:
                os.remove(path)
            eq_(path1, path_1)
            eq_(path2, path_2)
            eq_(diff_program, "opendiff")
            diffed.append(1)
        with tempdir() as tmp, test_app(config) as app, \
                replattr(mod, "external_diff", diff_stub):
            window = app.windows[0]
            editor = text_editor = window.projects[0].editors[0]
            if config == "editor":
                path = editor.file_path = join(tmp, "file.txt")
                with open(path, mode="w", encoding="utf8") as fh:
                    fh.write("abc")
            m = Mocker()
            text_view = editor.text_view = m.mock(TextView)
            path_1 = editor.file_path
            if original:
                make_dirty(editor.document)
                name_ext = splitext(test_app(app).name(editor))
                path_2 = Regex(r"/file-.*\.txt$")
                args = None
                text_view.string() >> "def"
            elif len(window.selected_items) == 2:
                editor2 = window.selected_items[1]
                editor2.text_view = m.mock(TextView)
                name_ext = splitext(test_app(app).name(editor)[7:-1])
                path_1 = Regex(r"/{}-.*{}$".format(*name_ext))
                name_ext = splitext(test_app(app).name(editor2)[7:-1])
                path_2 = Regex(r"/{}-.*{}$".format(*name_ext))
                args = None
                text_view.string() >> "def"
                editor2.text_view.string() >> "ghi"
            else:
                path_1 = join(tmp, "other.txt")
                path_2 = editor.file_path
                with open(path_1, mode="w", encoding="utf8") as fh:
                    fh.write("other")
                assert " " not in path_1, path_1
                args = mod.diff.arg_parser.parse(path_1)
            with m:
                mod.diff(editor, args)
                assert diffed
    yield test, True
    yield test, False
    yield test, False, "editor(doc_a.txt)* editor(doc_b.txt)*"

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
        eq_(sum(1 for c in command if c == ";"), 1, command)
        args = shlex.split(command.split(";")[0])
        print(args)
        eq_(args, ["true", "--arg", path, path])
        check_call(command, **kw)
        assert not exists(path), "test file not removed: {}".format(path)
    with tempdir() as tmp, replattr(mod, "Popen", popen):
        path = join(tmp, "file.txt")
        with open(path, mode="w") as fh:
            fh.write("abc")
        mod.external_diff(path, path, "true --arg", [path])
        assert popen_called, "diff command was not executed"
