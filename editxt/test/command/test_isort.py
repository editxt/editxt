# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2019 Daniel Miller <millerdev@gmail.com>
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
from os.path import isabs, join

from testil import eq_

import editxt.command.isort as mod
from editxt.test.test_commands import CommandTester
from editxt.test.util import tempdir, test_app


def test_isort_command():
    def test(command, selection=(0, 0), expect=None):
        if expect is None:
            expect = SORTED_IMPORTS
        text = UNSORTED_IMPORTS
        do = CommandTester(mod.sort_imports, text=text, sel=selection)
        do(command)
        eq_(str(do.editor.text), expect)

    yield test, "isort"
    yield test, "isort editxt", (0, 0), SORTED_EDITXT_IMPORTS
    yield test, "isort", (1, 119), """
import os
import sys

from editxt import Object, Object2, Object3

print("Hey")
""" + UNSORTED_IMPORTS[120:]


def test_default_package():
    with test_app("project(/dir) editor*") as app:
        tmp = test_app(app).tmp
        os.mkdir(join(tmp, "dir"))
        os.mkdir(join(tmp, "dir/package"))
        os.mkdir(join(tmp, "dir/other"))
        for path in [
            "dir/package/__init__.py",
            "dir/other/b.txt",
        ]:
            assert not isabs(path), path
            with open(join(tmp, path), "w") as fh:
                pass
        editor = app.windows[0].current_editor
        editor.updates_path_on_file_move = False

        def test(path, result=""):
            editor.file_path = 'file' if path is None else join(tmp, path)
            eq_(mod.default_package(editor), result)

        yield test, None
        yield test, "dir/mod.py"
        yield test, "dir/other/mod.py"
        yield test, "dir/package/mod.py", "package"


UNSORTED_IMPORTS = """
from editxt import Object

print("Hey")

import os

from editxt import Object3

from editxt import Object2

import sys

from third_party import lib15, lib1, lib2, lib3, lib4, lib5, lib6, lib7, lib8, lib9, lib10, lib11, lib12, lib13, lib14

import sys

from __future__ import absolute_import

from third_party import lib3

print("yo")
"""

SORTED_IMPORTS = """
from __future__ import absolute_import

import os
import sys

from editxt import Object, Object2, Object3
from third_party import (
    lib1,
    lib2,
    lib3,
    lib4,
    lib5,
    lib6,
    lib7,
    lib8,
    lib9,
    lib10,
    lib11,
    lib12,
    lib13,
    lib14,
    lib15,
)

print("Hey")









print("yo")
"""

SORTED_EDITXT_IMPORTS = """
from __future__ import absolute_import

import os
import sys

from third_party import (
    lib1,
    lib2,
    lib3,
    lib4,
    lib5,
    lib6,
    lib7,
    lib8,
    lib9,
    lib10,
    lib11,
    lib12,
    lib13,
    lib14,
    lib15,
)

from editxt import Object, Object2, Object3

print("Hey")









print("yo")
"""
