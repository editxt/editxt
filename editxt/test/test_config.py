# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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
from os.path import join
from nose.tools import eq_

import editxt.config as mod
import editxt.constants as const
from editxt.util import get_color
from editxt.test.util import assert_raises, CaptureLog, Regex, tempdir

SCHEMA = {
    "key": mod.String(),
    "answer": mod.Integer(),
}

def test_Config_init_with_no_file():
    with tempdir() as tmp:
        conf = mod.Config(tmp, SCHEMA)
        with assert_raises(KeyError):
            conf["key"]

def test_Config_init():
    with tempdir() as tmp:
        with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
            f.write("key: value\n")
        conf = mod.Config(tmp, SCHEMA)
        eq_(conf["key"], "value")

def test_Config_init_invalid_config():
    def test(config_data, error):
        with tempdir() as tmp, CaptureLog(mod) as log:
            with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
                f.write(config_data)
            conf = mod.Config(tmp, SCHEMA)
            with assert_raises(KeyError):
                conf["key"]
            regex = Regex("cannot load [^:]+/config\.yaml: {}".format(error))
            eq_(log.data, {"error": [regex]})

    yield test, "[key]", "root object is a list, expected a dict"
    yield test, "key:\n[value:", "while scanning a simple key"

def test_Config_reload():
    with tempdir() as tmp:
        with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
            f.write("key: value\n")
        conf = mod.Config(tmp, SCHEMA)
        eq_(conf["key"], "value")

        with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
            f.write("answer: 42\n")
        conf.reload()
        eq_(conf["answer"], 42)
        assert "key" not in conf, conf

def test_Config_schema():
    def test(data, key, value, errors={}):
        config = mod.Config("/tmp/missing.3216546841325465132546514321654")
        config.data = data

        with CaptureLog(mod) as log:
            if isinstance(value, Exception):
                with assert_raises(type(value), msg=str(value)):
                    config[key]
            else:
                eq_(config[key], value)
            eq_(log.data, errors)

    yield test, {}, "unknown", KeyError("unknown")
    yield test, {}, "unknown.sub", KeyError("unknown.sub")

    yield test, {}, "highlight_selected_text.enabled", True
    yield test, {"highlight_selected_text": {}}, \
        "highlight_selected_text.enabled", True
    yield test, {"highlight_selected_text": {"enabled": True}}, \
        "highlight_selected_text.enabled", True
    yield test, {"highlight_selected_text": []}, \
        "highlight_selected_text.enabled", True, \
        {"error": ["highlight_selected_text: expected dict, got []"]}
    yield test, {"highlight_selected_text": {"enabled": "treu"}}, \
        "highlight_selected_text.enabled", True, \
        {"error": ["highlight_selected_text.enabled: expected boolean, got 'treu'"]}
    yield test, {"highlight_selected_text": True}, \
        "highlight_selected_text.enabled", True, \
        {"error": ["highlight_selected_text: expected dict, got True"]}
    yield test, {}, "highlight_selected_text.enabled.x", \
        ValueError("highlight_selected_text.enabled.x: "
                   "highlight_selected_text.enabled is boolean, not a dict")

    yield test, {}, "indent.mode", const.INDENT_MODE_SPACE
    yield test, {"indent": {"mode": "xyz"}}, \
        "indent.mode", const.INDENT_MODE_SPACE, \
        {"error": ["indent.mode: expected one of (space|tab), got 'xyz'"]}

    yield test, {}, "indent.size", 4
    yield test, {"indent": {"size": "two"}}, "indent.size", 4, \
        {"error": ["indent.size: expected integer, got 'two'"]}
    yield test, {"indent": {"size": 0}}, "indent.size", 4, \
        {"error": ["indent.size: 0 is less than the minimum value (1)"]}

    yield test, {}, "newline_mode", const.NEWLINE_MODE_UNIX
    yield test, {"newline_mode": "xyz"}, \
        "newline_mode", const.NEWLINE_MODE_UNIX, \
        {"error": ["newline_mode: expected one of (LF|CR|CRLF|UNICODE), got 'xyz'"]}

    yield test, {}, "soft_wrap", const.WRAP_NONE
    yield test, {"soft_wrap": "xyz"}, \
        "soft_wrap", const.WRAP_NONE, \
        {"error": ["soft_wrap: expected one of (none|word), got 'xyz'"]}


def test_Type_validate():
    NOT_SET = mod.NOT_SET
    def test(Type, input, value, default=NOT_SET):
        if default is NOT_SET:
            type_ = Type()
        else:
            type_ = Type(default=default)
        if isinstance(value, Exception):
            with assert_raises(type(value), msg=str(value)):
                type_.validate(input, "key")
        else:
            eq_(type_.validate(input, "key"), value)

    yield test, mod.Boolean, True, True
    yield test, mod.Boolean, True, True
    yield test, mod.Boolean, False, False
    yield test, mod.Boolean, "true", True
    yield test, mod.Boolean, "false", False
    yield test, mod.Boolean, "yes", True
    yield test, mod.Boolean, "no", False
    yield test, mod.Boolean, NOT_SET, NOT_SET
    yield test, mod.Boolean, NOT_SET, True, True
    yield test, mod.Boolean, NOT_SET, None, None
    yield test, mod.Boolean, 42, ValueError("key: expected boolean, got 42")
    yield test, mod.Boolean, "null", \
        ValueError("key: expected boolean, got 'null'")

    yield test, mod.String, "true", "true"
    yield test, mod.String, NOT_SET, NOT_SET
    yield test, mod.String, NOT_SET, "abc", "abc"
    yield test, mod.String, NOT_SET, None, None
    yield test, mod.String, 42, ValueError("key: expected string, got 42")

    yield test, mod.Integer, 42, 42
    yield test, mod.Integer, NOT_SET, NOT_SET
    yield test, mod.Integer, NOT_SET, "abc", "abc"
    yield test, mod.Integer, NOT_SET, None, None
    yield test, mod.Integer, 'x', ValueError("key: expected integer, got 'x'")

    yield test, mod.Color, "FEFF6B", get_color("FEFF6B")
    yield test, mod.Color, "x", \
        ValueError("key: expected RRGGBB hex color string, got 'x'")

    yield test, mod.Enum, NOT_SET, NOT_SET
