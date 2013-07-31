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
import logging
from os.path import exists, join

import editxt.constants as const
from editxt.util import load_yaml

log = logging.getLogger(__name__)


class Config(dict):

    def __init__(self, profile_path):
        self.path = join(profile_path, const.CONFIG_FILENAME)
        self.reload()

    def reload(self):
        if exists(self.path):
            try:
                with open(self.path) as f:
                    data = load_yaml(f)
            except Exception as err:
                log.error("cannot load %s: %s", self.path, err)
                return
            else:
                if not isinstance(data, dict):
                    log.error("cannot load %s: root object is a %s, "
                        "expected a dict", self.path, type(data).__name__)
                    return
            self.clear()
            self.update(data)
        else:
            self.clear()
