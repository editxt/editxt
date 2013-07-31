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
from editxt.test.util import assert_raises, FakeLog, Regex, tempdir


def test_Config_init_with_no_file():
    with tempdir() as tmp:
        conf = mod.Config(tmp)
        with assert_raises(KeyError):
            conf["key"]

def test_Config_init():
    with tempdir() as tmp:
        with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
            f.write("key: value\n")
        conf = mod.Config(tmp)
        eq_(conf["key"], "value")

def test_Config_init_invalid_config():
    def test(config_data, error):
        with tempdir() as tmp, FakeLog(mod) as log:
            with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
                f.write(config_data)
            conf = mod.Config(tmp)
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
        conf = mod.Config(tmp)
        eq_(conf["key"], "value")

        with open(join(tmp, const.CONFIG_FILENAME), "w") as f:
            f.write("answer: 42\n")
        conf.reload()
        eq_(conf["answer"], 42)
        assert "key" not in conf, conf
