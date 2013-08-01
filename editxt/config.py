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

# The following schema defines the confuration values accepted by the program.
# Use function to allow config schema to be defined at top of file before
# schema types.
def config_schema(): return {
    "highlight_selected_text": {
        "enabled": Boolean(default=True),
        "color": Color(default=get_color("FEFF6B")),
    },
    "indent": {
        "mode": Enum(
            const.INDENT_MODE_SPACE,
            const.INDENT_MODE_TAB,
            default=const.INDENT_MODE_SPACE),
        "size": Integer(default=4, minimum=1),
    },
    "newline_mode": Enum(
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
        default=const.NEWLINE_MODE_UNIX),
    "wrap_mode": Enum(
        const.LINE_WRAP_NONE,
        const.LINE_WRAP_WORD,
        default=const.LINE_WRAP_NONE),
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


class Enum(Type):

    def __init__(self, *args, **kw):
        super(Enum, self).__init__(**kw)
        self.choices = choices = {}
        self.names = names = []
        for arg in args:
            if isinstance(arg, tuple):
                name, value = arg
            else:
                name = value = arg
            assert isinstance(name, basestring), \
                "choice name must be a string, got {!r}".foramt(name)
            choices[name] = value
            names.append(name)

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        try:
            return self.choices[value]
        except KeyError:
            raise ValueError("{}: expected one of ({}), got {!r}"
                .format(key, "|".join(self.names), value))


class Integer(Type):

    def __init__(self, *args, **kw):
        self.minimum = kw.pop("minimum", None)
        super(Integer, self).__init__(*args, **kw)

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        if isinstance(value, (int, long)):
            if self.minimum is not None and value < self.minimum:
                raise ValueError("{}: {} is less than the minimum value ({})"
                    .format(key, value, self.minimum))
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
            log.error("cannot parse color: %r", value, exc_info=True)
            raise ValueError("{}: expected RRGGBB hex color string, got {!r}"
                             .format(key, value))


class Config(object):

    def __init__(self, profile_path, schema=config_schema()):
        self.path = join(profile_path, const.CONFIG_FILENAME)
        self.data = {}
        self.valid = {}
        self.errors = {}
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
        self.errors = {}

    def __contains__(self, name):
        try:
            self[name]
        except (KeyError, ValueError):
            return False
        return True

    def __getitem__(self, name):
        try:
            return self.valid[name]
        except KeyError:
            if name in self.errors:
                raise self.errors[name]
        try:
            value = self.lookup(name)
        except (KeyError, ValueError) as err:
            self.errors[name] = err
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
                raise ValueError("{}: {} is {}, not a dict".format(
                    name, ".".join(so_far), type(schema).__name__.lower()))
            schema = schema.get(part)
            if schema is None:
                raise KeyError(name)
            if not isinstance(value, dict):
                log.error("%s: expected dict, got %r", ".".join(so_far), value)
                value = {}
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
        try:
            value = schema.validate(value, name)
        except Exception as err:
            if not str(err).startswith(name + ": "):
                log.error("%s: %s", name, error, exc_info=True)
            else:
                log.error(str(err))
            value = schema.default
        if value is NOT_SET:
            raise KeyError(name)
        return value
