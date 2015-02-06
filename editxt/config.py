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
import logging
from os.path import exists, join

import editxt.constants as const
from editxt.platform.font import DEFAULT_FONT
from editxt.util import get_color, hex_value, load_yaml

log = logging.getLogger(__name__)

NOT_SET = object()

# The following schema defines the confuration values accepted by the program.
# Use function to allow config schema to be defined at top of file before
# schema types.
def config_schema(): return {
    "diff_program": String("opendiff"),
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
    "font": {
        "face": String(default=DEFAULT_FONT.face),
        "size": Float(minimum=-1.0, default=DEFAULT_FONT.size),
        "smooth": Boolean(default=DEFAULT_FONT.smooth),
    },
    "newline_mode": Enum(
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
        default=const.NEWLINE_MODE_UNIX),
    "line_number_color": Color(default=get_color("707070")),
    "right_margin": {
        "position": Integer(default=const.DEFAULT_RIGHT_MARGIN, minimum=0),
        "line_color": Color(default=get_color("E6E6E6")),
        "margin_color": Color(default=get_color("F7F7F7")),
    },
    "soft_wrap": Enum(
        const.WRAP_NONE,
        const.WRAP_WORD,
        default=const.WRAP_NONE),
    "command": {
        # namespace for values added by @command decorated functions
    },
    "shortcuts": {
        # leading space -> not saved in command history
        "Command+Alt+Left": String(" doc  previous"),
        "Command+Alt+Right": String(" doc  next"),
        "Command+Alt+Up": String(" doc  up"),
        "Command+Alt+Down": String(" doc  down"),
    }
}


class Type(object):

    def __init__(self, default=NOT_SET):
        self.default = default

    def validate(self, value, key):
        raise NotImplementedError("abstract method")

    @property
    def default_string(self):
        return str(self.default)


class String(Type):

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        if isinstance(value, str):
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
            assert isinstance(name, str), \
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

    @property
    def default_string(self):
        for name in self.names:
            if self.choices[name] == self.default:
                return name
        return self.default


class Integer(Type):

    def __init__(self, *args, **kw):
        self.minimum = kw.pop("minimum", None)
        super(Integer, self).__init__(*args, **kw)

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        if isinstance(value, int):
            if self.minimum is not None and value < self.minimum:
                raise ValueError("{}: {} is less than the minimum value ({})"
                    .format(key, value, self.minimum))
            return value
        raise ValueError("{}: expected integer, got {!r}".format(key, value))


class Float(Type):

    def __init__(self, *args, **kw):
        self.minimum = kw.pop("minimum", None)
        super(Float, self).__init__(*args, **kw)

    def validate(self, value, key):
        if value is NOT_SET:
            return self.default
        if isinstance(value, int):
            value = float(value)
        if isinstance(value, float):
            if self.minimum is not None and value < self.minimum:
                raise ValueError("{}: {} is less than the minimum value ({})"
                    .format(key, value, self.minimum))
            return value
        raise ValueError("{}: expected float, got {!r}".format(key, value))


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

    @property
    def default_string(self):
        return "true" if self.default else "false"


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

    @property
    def default_string(self):
        return hex_value(self.default)


class Config(object):

    def __init__(self, path, schema=config_schema()):
        self.path = path
        self.data = {}
        self.valid = {}
        self.errors = {}
        self.schema = schema
        self.reload()

    def reload(self):
        if self.path and exists(self.path):
            try:
                with open(self.path) as f:
                    data = load_yaml(f)
            except Exception as err:
                log.error("cannot load %s: %s", self.path, err)
                return
            else:
                if data is None:
                    data = {}
                elif not isinstance(data, dict):
                    log.error("cannot load %s: root object is a %s, "
                        "expected a dict", self.path, type(data).__name__)
                    return
            log.info("loaded %s", self.path)
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

    def lookup(self, name, as_dict=False):
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
                value = value_of(schema)
            so_far.append(part)

        if isinstance(schema, dict):
            if not isinstance(value, dict):
                log.error("%s: expected dict, got %r", ".".join(so_far), value)
                value = schema_to_dict(schema)
            if as_dict:
                return value
            config = Config(None, schema)
            config.data = value
            return config
        try:
            value = schema.validate(value, name)
        except Exception as err:
            if not str(err).startswith(name + ": "):
                log.error("%s: %s", name, err, exc_info=True)
            else:
                log.error(str(err))
            value = schema.default
        if value is NOT_SET:
            raise KeyError(name)
        return value

    def extend(self, name, schema, namespace="command"):
        command_schema = self.schema["command"]
        if name in command_schema:
            command_schema[name].update(schema)
        else:
            command_schema[name] = schema

    def for_command(self, name):
        return self["command.{}".format(name)]

    @property
    def default_config(self):
        def get_lines(schema, level=0):
            for key, value in sorted(schema.items()):
                if isinstance(value, Type):
                    yield "#{indent}{key}: {val}".format(
                        indent="  " * level,
                        key=key,
                        val=value.default_string
                    )
                elif value is NOT_SET:
                    pass
                else:
                    yield "#{}{}:".format("  " * level, key)
                    for line in get_lines(value, level + 1):
                        yield line
            yield ""
        return "\n".join(get_lines(self.schema))


def value_of(cfg):
    if isinstance(cfg, dict):
        return schema_to_dict(cfg)
    return cfg.default

def schema_to_dict(schema):
    return {key: value_of(cfg) for key, cfg in schema.items()}
