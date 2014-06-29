# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
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
import sys
from importlib import import_module
from logging import StreamHandler as console_log_handler


def init(platform, use_pdb):
    modules = [
        "constants",
        "logging",
        "main",
        "kvo",

        "app",
        "document",
        "events",
        "views",
        "window",
    ]

    import_module("{}.{}".format(__name__, platform))
    main = import_module("{}.{}.main".format(__name__, platform))
    main.init(use_pdb)

    self = sys.modules[__name__]
    for name in modules:
        module = import_module("{}.{}.{}".format(__name__, platform, name))
        sys.modules[__name__ + "." + name] = module
        setattr(self, name, module)

    if not sys.stderr.isatty():
        self.console_log_handler = self.logging.PlatformLogHandler
