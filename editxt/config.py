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
from editxt.util import get_color, load_yaml

log = logging.getLogger(__name__)

NOT_SET = object()


def config_schema(): return {
    "selection_matching": {
        "enabled": Boolean(default=True),
        "color": Color(default="FEFF6B"),
    }
}


class Type(object):

    def __init__(self, default=NOT_SET):
        self.default = default

    def validate(self, value, key):
        raise NotImplementedError("abstract method")


class String(Type):

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        if isinstance(value, basestring):
            if not isinstance(value, unicode):
                value = value.decode("utf-8")
            return value
        raise ValueError("{}: expected string, got {!r}".format(key, value))


class Integer(Type):

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        if isinstance(value, (int, long)):
            return value
        raise ValueError("{}: expected integer, got {!r}".format(key, value))


class Boolean(Type):

    VALUES = {
        True: True,
        False: False,
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
    }

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        try:
            return self.VALUES[value]
        except KeyError:
            raise ValueError(
                "{}: expected boolean, got {!r}".format(key, value))


class Color(Type):

    def validate(self, value, key):
        if value is NOT_SET:
            value = self.default
            if value is NOT_SET:
                return value
        try:
            return get_color(value)
        except Exception:
            log.warn("cannot parse color: %r", value, exc_info=True)
            raise ValueError("{}: expected RRGGBB hex color string, got {!r}"
                             .format(key, value))


class Config(object):

    def __init__(self, profile_path, schema=config_schema()):
        self.path = join(profile_path, const.CONFIG_FILENAME)
        self.data = {}
        self.valid = {}
        self.schema = schema
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
            self.data = data
        else:
            self.data = {}
        self.valid = {}

    def __contains__(self, name):
        try:
            self[name]
        except (KeyError, ValueError):
            return False
        return True

    def __getitem__(self, name):
        try:
            value = self.valid[name]
        except KeyError:
            pass
        else:
            if isinstance(value, Exception):
                raise value
            return value
        try:
            value = self.lookup(name)
        except (KeyError, ValueError) as err:
            self.valid[name] = err
            raise
        self.valid[name] = value
        return value

    def lookup(self, name):
        value = self.data
        schema = self.schema
        assert isinstance(schema, dict), schema
        so_far = []
        for part in name.split("."):
            if not isinstance(schema, dict):
                raise ValueError(
                    "{}: {} is not a dict".format(name, ".".join(so_far)))
            schema = schema.get(part)
            if schema is None:
                raise KeyError(name)
            if not isinstance(value, dict):
                raise ValueError("{}: expected dict, got {!r}"
                                 .format(".".join(so_far), value))
            try:
                value = value[part]
            except KeyError:
                if isinstance(schema, dict):
                    value = {}
                else:
                    value = schema.default
            so_far.append(part)

        if isinstance(schema, dict):
            if not isinstance(value, dict):
                raise ValueError(
                    "{}: expected dict, got {!r}".format(name, value))
            raise NotImplementedError
        value = schema.validate(value, name)
        if value is NOT_SET:
            raise KeyError(name)
        return value
