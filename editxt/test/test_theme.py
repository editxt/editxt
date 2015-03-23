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
import editxt.constants as const
import editxt.theme as mod
from editxt.config import Config
from editxt.util import get_color
from editxt.test.test_config import configify
from editxt.test.util import assert_raises, CaptureLog, eq_

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
