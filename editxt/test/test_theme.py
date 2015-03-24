# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2015 Daniel Miller <millerdev@gmail.com>
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
import editxt.theme as mod
from editxt.config import Config, ColorString
from editxt.test.test_config import configify
from editxt.test.util import assert_raises, eq_, replattr

def test_Theme_selection_secondary_color():
    # currently theme.selection_secondary_color is not used
    config = Config(None)
    theme = mod.Theme(config)
    def test(name):
        # the default depends on a system color (user preference)
        assert theme.selection_secondary_color is not None
    yield test, "default theme.selection_secondary_color"

    def test(name):
        config.reload()
        config.data = configify({"theme.selection_secondary_color": "CACAFE"})
        theme.reset()
        eq_(mod.hex_value(theme.selection_secondary_color), "CACAFE")
    yield test, "config theme.selection_secondary_color"

    def test(name):
        config.reload()
        config.data = configify({"theme.selection_color": "A6CAFE"})
        theme.reset()
        eq_(mod.hex_value(theme.selection_secondary_color), "CACACA")
    yield test, "derived theme.selection_secondary_color"

def test_Theme_get_syntax_color():
    config = Config(None, { "theme": {
        "text_color": ColorString("000000"),
        "syntax": { "default": {
            "builtin": ColorString("bbbbbb"),
            "comment": ColorString("cccccc"),
            "keyword": ColorString("eeeeee"),
            "string": ColorString("accafe"),
        }},
    }})
    config.data = {"theme": {"syntax": {
        "default": {
            "comment": "112233",
            "keyword": "445566",
        },
        "C": {
            "builtin": "665544",
            "keyword": "332211",
        },
    }}}
    theme = mod.Theme(config)
    get_color = lambda v: v
    def test(name, color):
        with replattr(mod, "get_color", get_color, sigcheck=False):
            eq_(theme.get_syntax_color(name), color)
    yield test, "A builtin", "bbbbbb"
    yield test, "A comment", "112233"
    yield test, "A keyword", "445566"
    yield test, "A string", "accafe"
    yield test, "C builtin", "665544"
    yield test, "C comment", "112233"
    yield test, "C keyword", "332211"
    yield test, "C string", "accafe"
