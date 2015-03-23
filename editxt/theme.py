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
from editxt.config import Color, NOT_SET
from editxt.util import get_color, hex_value, rgb2gray


class Theme(object):

    class derived:
        def selection_secondary_color(config):
            """Unused proof of concept

            Derived theme value that can be overridden in the config
            """
            value = config.get("theme.selection_secondary_color", Color(None))
            if value is None:
                color = hex_value(config["theme.selection_color"])
                value = get_color(rgb2gray(color))
            return value

    def __init__(self, config):
        self.config = config
        self.cached = set()
        self.reset()

    def reset(self):
        self.syntax = self.config.lookup("theme.syntax", True)
        self.default = self.syntax.get("default", {})
        for name in self.cached:
            delattr(self, name)
        self.cached.clear()

    def __getattr__(self, name):
        try:
            value = self.config["theme." + name]
        except KeyError:
            value = getattr(self.derived, name)(self.config)
        self.cached.add(name)
        setattr(self, name, value)
        return value

    def __getitem__(self, name):
        return getattr(self, name)

    def get_syntax_color(self, name):
        try:
            value = self.default[name]
        except KeyError:
            lang, token_name = name.rsplit(" ", 1)
            if token_name:
                value = self._get(lang, token_name)
                if value is None:
                    value = self._get("default", token_name)
            else:
                value = None
            self.default[name] = value
        return value

    def _get(self, lang, name):
        data = self.syntax.get(lang)
        if data:
            while name:
                try:
                    return data[name]
                except KeyError:
                    pass
                name = name.rpartition(".")[0]
        return None
