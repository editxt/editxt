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
"""
Command parser specification:

- Arguments are space-delimited.
- Arguments must be in order.
- Argument names must be valid Python identifiers.
- Some examples:

    CommandParser(
        Choice('selection all'),
        Choice(('forward', False), ('reverse', True), name='reverse'),
    )
    matches:
        'selection reverse' : selection = 'selection',  reverse = True
        'sel rev'           : selection = 'selection',  reverse = True
        's r'               : selection = 'selection',  reverse = True
        'all reverse'       : selection = 'all',        reverse = True
        'a f'               : selection = 'all',        reverse = False
        ''                  : selection = 'selection',  reverse = False

    CommandParser(
        Regex('regex'),
        Choice(('no-opt', False), ('opt', True), name='opt'),
        Int('num'),
    )
    matches:
        '/^abc$/ opt 123'
        '/^abc$/ o 123'
        '/^abc$/o 123'

- An arguments may be skipped by entering an extra space:

    CommandParser(
        Choice(('yes', True), ('no', False), name='bool'),
        Regex('regex'),
        Int('num', default=42),
    )
    matches:
        'y'         : bool = True, regex = None, num = 42
        ' /abc/ 1'  : bool = None, regex = 'abc', num = 1
        ' /abc/'    : bool = None, regex = 'abc', num = None
        '  1'  : bool = False, regex = None, num = 1
"""
import os
import re
from functools import partial
from itertools import chain

from editxt.util import user_path


class CommandParser(object):
    """Text command parser

    :params *argspec: Argument specifiers.
    """

    def __init__(self, *argspec, context=None):
        self.argspec = argspec
        self.context = context
        # TODO assert no duplicate arg names

    def with_context(self, *args, **kw):
        """Get a new command parser with the given context

        See ``Field.with_context`` for argument specification.
        """
        argspec = [arg.with_context(*args, **kw) for arg in self.argspec]
        return CommandParser(*argspec)

    def match(self, text, index=0):
        """Check if first argument can consume text at index

        :rtype: boolean
        """
        try:
            self.argspec[0].consume(text, index)
        except (ParseError, ArgumentError):
            return False
        return True

    def tokenize(self, text, index, args=None):
        """Generate a sequence of parsed arguments

        :param text: Argument string.
        :param index: Start tokenizing at this index in text.
        :param args: Optional object on which to set accumulated
        argument value attributes.
        :yields: A sequence of ``Arg`` objects. If there is leftover
        text after all arguments have been parsed the last generated
        arg will contain the remaining text with ``field = None``.
        """
        if args is None:
            args = Options()
        for field in self.argspec:
            try:
                arg = Arg(field, text, index, args)
                yield arg
                if not arg.errors:
                    index = arg.end
            except SkipField as skip:
                arg = skip
            setattr(args, field.name, arg.value)
        if index < len(text):
            yield Arg(None, text, index, args)

    def parse(self, text, index=0):
        """Parse arguments from the given text

        :param text: Argument string.
        :param index: Start parsing at this index in text.
        :raises: `ArgumentError` if the text string is invalid.
        :returns: `Options` object with argument values as attributes.
        """
        opts = Options()
        errors = []
        for arg in self.tokenize(text, index, opts):
            if arg.field is None:
                if errors:
                    break
                msg = 'unexpected argument(s): ' + str(arg)
                raise ArgumentError(msg, opts, [], arg.start)
            if not arg.errors:
                if errors:
                    del errors[:]
            else:
                errors.extend(arg.errors)
        if errors:
            msg = 'invalid arguments: {}'.format(text)
            raise ArgumentError(msg, opts, errors)
        return opts

    def default_options(self):
        return Options(**{field.name: field.default for field in self.argspec})

    def get_placeholder(self, text, index=0):
        """Get placeholder string to follow the given command text

        :param text: Argument string.
        :returns: A string of placeholder text, which can be used as a
            hint about remaining arguments to be entered.
        """
        values = []
        for arg in self.tokenize(text, index):
            if not arg.could_consume_more:
                continue
            value = arg.get_placeholder()
            if value is not None:
                values.append(value)
        return " ".join(values)

    def get_completions(self, text, index=0):
        """Get completions for the given command text

        :param text: Argument string.
        :param index: Index in ``text`` to start parsing.
        :returns: A list of possible values to complete the command.
        """
        for arg in self.tokenize(text, index):
            if arg.field is None:
                return []
            if arg.could_consume_more:
                # TODO what if arg has errors? is raw reliable?
                return arg.get_completions()
        return []

    def get_help(self, text):
        raise NotImplementedError

    def arg_string(self, options, strip=True):
        """Compile command string from options

        :param options: Options object.
        :returns: Command argument string.
        :raises: Error
        """
        args = []
        for field in self.argspec:
            try:
                value = getattr(options, field.name)
            except AttributeError:
                raise Error("missing option: {}".format(field.name))
            args.append(field.arg_string(value))
        return " ".join(args).rstrip(" ") if strip else " ".join(args)


class Arg(object):
    """An argument parsed from a command string

    Important attributes:

    - `field` : Field that consumed this argument. Can be `None`.
    - `text` : Full command string.
    - `start` : Index of the first consumed character.
    - `end` : Index of the last consumed character.
    - `value` : Parsed argument value. Its type depends on `field`.
    - `errors` : Errors raised while consuming the argument.
    - `preceding` : `Options` object containing preceding argument values.

    """

    def __init__(self, field, text, index, preceding):
        self.field = field
        self.text = text
        self.start = start = index
        self.errors = []
        self.preceding = preceding
        if field is None:
            value = None
            index = len(text)
            assert index > start, (text, start, index)
        elif self.start > len(text):
            value = field.default
            index = start
        else:
            try:
                value, index = field.consume(text, start)
                if index == len(text) and not text[start:].endswith(" "):
                    # this argument could consume more characters
                    index += 1
            except ParseError as err:
                self.errors.append(err)
                value = field.default
                index = err.parse_index
            except ArgumentError as err:
                assert err.errors, "unexpected {!r}".format(err)
                self.errors.extend(err.errors)
                value = field.default
                index = err.errors[-1].parse_index
        self.end = index
        if field is not None:
            value = field.value_of(value, self)
        self.value = value

    def __repr__(self):
        if hasattr(self, "end"):
            plus = "+" if self.could_consume_more else ""
            return "<{} {!r}{}>".format(type(self).__name__, str(self), plus)
        return super().__repr__()

    def __str__(self):
        """Return the portion of the argument string consumed by this arg

        Does not include the space between this and the next arg even
        though that space is consumed by this arg.
        """
        start, end = self.start, self.end
        if start == end:
            return ""
        if self.could_consume_more:
            end -= 1
        return self.text[start:end]

    def __len__(self):
        """Return the length of this arg in the command string

        Does not include the space between this and the next arg even
        though that space is consumed by this arg.
        """
        start, end = self.start, self.end
        if start == end:
            return 0
        if self.could_consume_more:
            end -= 1
        return end - start

    @property
    def could_consume_more(self):
        """Return true if this arg could consume more characters if present
        """
        return self.end > len(self.text)

    def consume_token(self, index=None):
        """Consume one space-delimited token from the command string

        This consumes all text up to (including) the next space in the
        command string. The returned value will not contain spaces. If
        the character at index is a space, then first element of the
        returned tuple will be `None` indicating that the argument
        should use its default value. This is meant to be called by
        subclasses; it is not part of the public interface.

        :param index: Optional index from which to consume; defaults to the
        start of this arg.
        :returns: A tuple `(<token>, <index>)` where `token` is the
        consumed string (`None` if there was nothing to consume), and
        `index` is that following the last consumed character.
        """
        if isinstance(self, Arg):
            text = self.text
            if index is None:
                index = self.start
        else:
            text = self
        if index > len(text):
            return None, index
        if index == len(text) or text[index] == ' ':
            return None, index + 1
        end = text.find(' ', index)
        if end < 0:
            token = text[index:]
            end = len(text)
        else:
            token = text[index:end]
        return token, end + 1

    def get_placeholder(self):
        return self.field.get_placeholder(self)

    def get_completions(self):
        index = self.start
        words = self.field.get_completions(self)
        for i, word in enumerate(words):
            if getattr(word, 'start', None) is not None:
                word.start += index
            else:
                words[i] = CompleteWord(word, start=index)
        return words


IDENTIFIER_PATTERN = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')

def identifier(name):
    ident = name.replace('-', '_')
    if not IDENTIFIER_PATTERN.match(ident):
        raise ValueError('invalid name: %s' % name)
    return ident


class Field(object):
    """Base command argument type used to parse argument values"""

    def __init__(self, name, default=None):
        if not hasattr(self, 'args'):
            self.args = [name, default]
        if not hasattr(self, 'placeholder'):
            self.placeholder = name
        self.name = identifier(name)
        self.default = default

    def with_context(self, editor):
        """Return a Field instance with editor (and history?) context

        The returned field object may be the same instance as the original
        on which this method was invoked.

        :param editor: The editor for which the command is being invoked.
        """
        return self

    def __eq__(self, other):
        if not issubclass(type(self), type(other)):
            return False
        return self.args == other.args

    def __str__(self):
        return self.placeholder

    def __repr__(self):
        argnames = self.__init__.__func__.__code__.co_varnames
        defaults = self.__init__.__func__.__defaults__ or []
        assert argnames[0] == 'self', argnames
        #assert len(self.args) == len(argnames) - 1, self.args
        args = []
        for name, default, value in zip(
                reversed(argnames), reversed(defaults), reversed(self.args)):
            if default != value:
                args.append('{}={!r}'.format(name, value))
        slice = -len(defaults) or None
        args.extend(repr(a) for a in reversed(self.args[:slice]))
        return '{}({})'.format(type(self).__name__, ', '.join(reversed(args)))

    def consume(self, text, index):
        """Consume argument value from text starting at index

        This consumes the argument value plus a trailing space
        (if present).

        :param text: Text from which to consume argument value.
        :param index: Index into text from which to start consuming.
        :raises: ParseError if argument could not be consumed.
        :returns: A tuple `(<argument value>, <index>)` where `index` is
            that following the last consumed character in `text`.
            `index` is one more than the length of the given `text` if
            all remaining characters were consumed forming a valid token
            but the presence of any other character would extend the
            consumed token.
        """
        raise NotImplementedError("abstract method")

    def value_of(self, consumed, arg):
        """Convert consumed result to argument value

        :param consumed: The first item in the tuple returned by
        `self.consume(...)`.
        :param arg: The `Arg` object.
        :returns: The argument value.
        :raises: `SkipField` to cause this field to be skipped.
        """
        return consumed

    def get_placeholder(self, arg):
        """Get placeholder string for this argument

        :param arg: An ``Arg`` object.
        :returns: A placeholder string.
        """
        return "" if arg else str(self)

    def get_completions(self, arg):
        """Get a list of possible completions for text

        :param arg: An ``Arg`` object.
        :returns: A list of possible completions for given arg.
        The ``start`` attribute of ``CompleteWord`` objects in the
        returned list may be set to an offset into the original
        token where the completion should start.
        """
        return []

    def arg_string(self, value):
        """Convert parsed value to argument string"""
        raise NotImplementedError("abstract method")


class Choice(Field):
    """A multiple-choice argument type

    Choices are names without spaces. At least one choice name is
    required, more are usually provided.

    :param *choices: Two or more choice names or name/value pairs. Choices
    may be specified as a single space-delimited string, or one or more
    positional arguments consisting of either strings, or tuples in the
    form ("name-string", <value>). The value is the name in the case
    where name/value pairs are not given. The first choice is the
    default.
    :param name: Optional name, defaults to the first choice name. Must
    be specified as a keyword argument.
    """

    def __init__(self, *choices, **kw):
        self.args = choices
        self.kwargs = kw.copy()
        if len(choices) == 1 and isinstance(choices[0], str):
            choices = choices[0].split()
        if len(choices) < 2:
            raise ValueError('at least two choices are required')
        self.mapping = map = {}
        self.reverse_map = {}
        self.names = names = []
        self.alternates = alts = []
        for choice in choices:
            if isinstance(choice, str):
                if " " in choice:
                    name = choice
                    value = choice.split()[0]
                else:
                    name = value = choice
            else:
                try:
                    name, value = choice
                except (TypeError, ValueError):
                    raise ValueError("invalid choice: %r" % (choice,))
                if not isinstance(name, str):
                    raise ValueError("invalid choice name: %r" % (name,))
            for i, name in enumerate(name.split()):
                if i == 0:
                    names.append(name)
                    self.reverse_map[value] = name
                else:
                    alts.append(name)
                if name in map:
                    raise ValueError("ambiguous name: %r" % (name,))
                map[name] = value
                for i in range(1, len(name)):
                    key = name[:i]
                    if key in names or key in alts:
                        raise ValueError("ambiguous name: %r" % (key,))
                    if key in map:
                        map.pop(key)
                    else:
                        map[key] = value
        self.placeholder = names[0]
        super(Choice, self).__init__(kw.pop('name', names[0]), map[names[0]])
        if kw:
            raise ValueError("unexpected arguments: %r" % (kw,))

    def __eq__(self, other):
        if not issubclass(type(self), type(other)):
            return False
        return self.args == other.args and self.kwargs == other.kwargs

    def __repr__(self):
        args = [repr(a) for a in self.args]
        args.extend('{}={!r}'.format(name, value)
                    for name, value in sorted(self.kwargs.items()))
        return '{}({})'.format(type(self).__name__, ', '.join(args))

    def consume(self, text, index):
        """Consume a single choice name starting at index

        The token at index may be a complete choice name or a prefix
        that uniquely identifies a choice. Return the default (first)
        choice value if there is no token to consume.

        :returns: (<chosen or default value>, <index>)
        """
        token, end = Arg.consume_token(text, index)
        if token is None:
            return self.default, end
        if token in self.mapping:
            return self.mapping[token], end
        names = ', '.join(n
            for n in chain(self.names, self.alternates)
            if n.startswith(token))
        if names:
            msg = '{!r} is ambiguous: {}'.format(token, names)
        else:
            end = index + len(token)
            names = ', '.join(self.names)
            msg = '{!r} does not match any of: {}'.format(token, names)
        raise ParseError(msg, self, index, end)

    def get_placeholder(self, arg):
        if not arg:
            return str(self)
        names = arg.get_completions()
        if not names:
            placeholder = ""
        elif len(names) == 1:
            placeholder = names[0][len(arg):]
        else:
            placeholder = "..."
        return placeholder

    def get_completions(self, arg):
        """List choice names that complete token"""
        token = str(arg)
        names = [n for n in self.names if n.startswith(token)]
        return names or [n for n in self.alternates if n.startswith(token)]

    def arg_string(self, value):
        if value == self.default:
            return ""
        try:
            return self.reverse_map[value]
        except KeyError:
            raise Error("invalid value: {}={!r}".format(self.name, value))


class Int(Field):

    def consume(self, text, index):
        """Consume an integer value

        :returns: (<int or default value>, <index>)
        """
        token, end = Arg.consume_token(text, index)
        if token is None:
            return self.default, end
        try:
            return int(token), end
        except (ValueError, TypeError) as err:
            raise ParseError(str(err), self, index, index + len(token))

    def get_placeholder(self, arg):
        if not arg:
            if isinstance(self.default, int):
                return str(self.default)
            return str(self)
        return ""

    def arg_string(self, value):
        if value == self.default:
            return ""
        if isinstance(value, int):
            return str(value)
        raise Error("invalid value: {}={!r}".format(self.name, value))


class String(Field):

    ESCAPES = {
        '\\': '\\',
        "'": "'",
        '"': '"',
        'a': '\a',
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        't': '\t',
        'v': '\v',
    }
    DELIMITERS = '"\''

    def consume(self, text, index):
        """Consume a string value

        :returns: (<string or default value>, <index>)
        """
        if index >= len(text):
            return self.default, index
        escapes = self.ESCAPES
        if text[index] not in self.DELIMITERS:
            delim = ' '
            start = index
            escapes = escapes.copy()
            escapes[' '] = ' '
        else:
            delim = text[index]
            start = index + 1
        chars, esc = [], 0
        for i, c in enumerate(text[start:]):
            if esc:
                esc = 0
                try:
                    chars.append(escapes[c])
                    continue
                except KeyError:
                    chars.append('\\')
            elif c == delim:
                if delim != ' ' and text[start + i + 1:start + i + 2] == ' ':
                    start += 1 # consume trailing space
                return ''.join(chars), start + i + 1
            if c == '\\':
                esc = 1
            else:
                chars.append(c)
        if delim == ' ':
            if not esc:
                return ''.join(chars), len(text) + 1
            delim = ''
        msg = 'unterminated string: {}{}'.format(delim, text[start:])
        raise ParseError(msg, self, index, len(text))

    def arg_string(self, value):
        if value == self.default:
            return ""
        if not isinstance(value, str):
            raise Error("invalid value: {}={!r}".format(self.name, value))
        value = value.replace("\\", "\\\\")
        for char, esc in self.ESCAPES.items():
            if esc in value and esc not in """\\"'""":
                value = value.replace(esc, "\\" + char)
        if " " in value or value.startswith(("'", '"')):
            return Regex.delimit(value, delimiters=""""'""")[0]
        return value


class File(String):
    """File path field

    :param name: Argument name.
    :param directory: If true, auto-complete directories only. Default false.
    """

    def __init__(self, name, directory=False, _editor=None):
        self.args = [name, directory, _editor]
        self.directory = directory
        self.editor = _editor
        super().__init__(name)

    def with_context(self, editor):
        return File(
            self.name,
            directory=self.directory,
            _editor=editor,
        )

    @property
    def path(self):
        if self.editor is None:
            return None
        return self.editor.dirname()

    def consume(self, text, index):
        """Consume a file path

        :returns: (<path>, <index>)
        """
        path, stop = super().consume(text, index)
        if path is None:
            return path, stop
        if path.startswith('~'):
            path = os.path.expanduser(path)
        if os.path.isabs(path):
            return path, stop
        if self.path is None:
            raise Error("cannot make absolute path (no context): {}".format(path))
        return os.path.join(self.path, path), stop

    def get_completions(self, arg):
        from os.path import exists, expanduser, isabs, isdir, join, sep, split
        token = super().consume(arg.text, arg.start)[0] or ""
        if token == '~':
            return [CompleteWord('~/', (lambda:''))]
        if token.startswith('~'):
            original_length = len(token)
            token = expanduser(token)
            diff = len(token) - original_length
        else:
            diff = 0
        if isabs(token):
            base = "/"
            path = token
        elif self.path is None:
            return []
        else:
            base = self.path
            path = join(base, token)
            diff += len(base) + 1
        root, name = split(path)
        assert len(base) <= len(root), (base, root)
        if not exists(root):
            return []
        assert len(sep) == 1, sep

        def delim(word):
            word = word.replace(' ', '\\ ')
            def get_delimiter():
                return "/" if isdir(join(root, word)) else " "
            return CompleteWord(word, get_delimiter, len(root) + 1 - diff)

        if not name:
            match = lambda n: not n.startswith(".")
        elif name.islower():
            def match(n, name=name.lower()):
                return n.lower().startswith(name)
        else:
            # edge case: when first match begins with a capital letter and
            # user types that letter then TAB ... typed letter is converted
            # to upper-case, which switches to the other matcher
            def match(n):
                return n.startswith(name)

        if self.directory:
            names = next(os.walk(root))[1]
        else:
            names = os.listdir(root)
        names = [delim(n) for n in sorted(names, key=str.lower) if match(n)]
        if isdir(path) and (name == ".." or name in names):
            if name in names:
                names.remove(name)
            names.append(CompleteWord(name + "/", lambda:"", len(root) + 1 - diff))
        return CompletionsList(names, title=user_path(root))

    def arg_string(self, value):
        if self.path is None:
            raise Error("cannot get arg string (no context): {}".format(value))
        if value and value.endswith((os.path.sep, "/")):
            raise Error("not a file: {}={!r}".format(self.name, value))
        if value.startswith(os.path.join(self.path, "")):
            value = value[len(self.path) + 1:]
        else:
            home = os.path.expanduser("~/")
            if value.startswith(home):
                value = "~/" + value[len(home):]
        return super().arg_string(value)


class RegexPattern(str):

    __slots__ = ["_flags"]
    DEFAULT_FLAGS = re.UNICODE | re.MULTILINE

    def __new__(cls, value="", flags=0, default_flags=DEFAULT_FLAGS):
        obj = super(RegexPattern, cls).__new__(cls, value)
        obj._flags = flags | default_flags
        return obj

    @property
    def flags(self):
        return self._flags

    def __hash__(self):
        return super(RegexPattern, self).__hash__() ^ hash(self._flags)

    def __repr__(self):
        return super(RegexPattern, self).__repr__() + Regex.repr_flags(self)

    def __eq__(self, other):
        streq = super(RegexPattern, self).__eq__(other)
        if streq and isinstance(other, RegexPattern):
            return self.flags == other.flags
        return streq

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        strlt = super(RegexPattern, self).__lt__(other)
        if not strlt and isinstance(other, RegexPattern) \
                and super(RegexPattern, self).__eq__(other):
            return self.flags < other.flags
        return strlt

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other


class Regex(Field):

    DELIMITERS = "/:\"'"

    def __init__(self, name, replace=False, default=None, flags=0):
        self.args = [name, replace, default, flags]
        self.replace = replace
        self.flags = flags
        default = (None, None) if replace and default is None else default
        super(Regex, self).__init__(name, default)

    def consume(self, text, index, _default=None):
        """Consume regular expression and optional replacement string and flags

        :returns: (<value>, <index>) where value is one of the following:
            replace     value
            False       <RegexPattern>
            True        (<RegexPattern>, <replacement string>)
        Either <RegexPattern> or <replacement string> may be the
        respective portion of the default value if not present.
        """
        if index > len(text):
            return self.default, index
        if index == len(text):
            return self.default, index + 1
        if self.replace and text[index] not in self.DELIMITERS:
            msg = "invalid search pattern: {!r}".format(text[index:])
            raise ParseError(msg, self, index, index)
        expr, index = self.consume_expression(text, index)
        if self.replace:
            if _default is None:
                _default = self.default
            if index > len(text):
                index = len(text) + 1 # to show we would consume more
                return (RegexPattern(expr, self.flags), _default[1]), index
            repl, index = self.consume_expression(text, index - 1)
            flags, index = self.consume_flags(text, index)
            return (RegexPattern(expr, flags), repl), index
        flags, index = self.consume_flags(text, index)
        return RegexPattern(expr, flags), index

    def consume_expression(self, text, index):
        if self.replace or text[index] in self.DELIMITERS:
            delim = text[index]
            delim_offset = 0
        else:
            delim = ' '
            delim_offset = -2
        chars, esc = [], 0
        i = -1
        for i, c in enumerate(text[index + 1 + (delim_offset // 2):]):
            if esc:
                esc = 0
                chars.append(c)
                continue
            elif c == delim:
                return ''.join(chars), index + i + 2 + delim_offset
            chars.append(c)
            if c == '\\':
                esc = 1
        if not esc:
            return ''.join(chars), index + i + 3 + delim_offset
        token = ''.join(chars)
        msg = 'unterminated regex: {}{}'.format(delim, token)
        raise ParseError(msg, self, index, len(text) + 1)

    def consume_flags(self, text, index):
        flags = {'i': re.IGNORECASE, 's': re.DOTALL, 'l': re.LOCALE}
        value = self.flags
        while index < len(text):
            char = text[index].lower()
            if char in flags:
                value |= flags[char]
            elif char == ' ':
                return value, index + 1
            else:
                c = text[index]
                msg = 'unknown flag: {}'.format(c)
                raise ParseError(msg, self, index, index)
            index += 1
        return value, index + (0 if index > len(text) else 1)

    def get_placeholder(self, arg):
        if not arg:
            return str(self)
        text = arg.text
        index = arg.start
        if self.replace and text[index] not in self.DELIMITERS:
            msg = "invalid search pattern: {!r}".format(text[index:])
            raise ParseError(msg, self, index, index)
        delim = text[index]
        ignore, index = self.consume_expression(text, index)
        if self.replace:
            if index > len(text):
                return delim * 2
            ignore, index = self.consume_expression(text, index - 1)
        return delim if index > len(text) else ""

    @classmethod
    def delimit(cls, value, allchars=None, delimiters=DELIMITERS):
        """Add delimiters before and after (escaped) value

        :param value: String to delimit.
        :param allchars: Characters to consider when choosing delimiter.
        Defaults to `value`.
        :param delimiters: A sequence of possible delimiters.
        :returns: (<delimited value>, delimiter)
        """
        if allchars is None:
            allchars = value
        delims = []
        for delim in delimiters:
            count = allchars.count(delim)
            if not count:
                break
            delims.append((count, delim))
        else:
            delim = min(delims)[1]
            value = cls.escape(value, delim)
        return "".join([delim, value, delim]), delim

    @classmethod
    def escape(cls, value, delimiter):
        """Escape delimiters in value"""
        return re.subn(r"""
            (
                (?:
                    \A          # beginning of string
                    |           # or
                    [^\\]       # not a backslash
                    |           # or
                    (?<={0})    # boundary after previous delimiter
                )
                (?:\\\\)*       # exactly 0, 2, 4, ... backslashes
            )
            {0}                 # delimiter
            """.format(delimiter),
            r"\1\\" + delimiter,
            value,
            flags=re.UNICODE | re.VERBOSE
        )[0]

    @classmethod
    def repr_flags(cls, value):
        if not value.flags:
            return ""
        chars = []
        if value.flags & re.IGNORECASE:
            chars.append("i")
        if value.flags & re.DOTALL:
            chars.append("s")
        if value.flags & re.LOCALE:
            chars.append("l")
        return "".join(chars)

    def arg_string(self, value):
        if value == self.default:
            return ""
        if self.replace:
            if not (isinstance(value, (tuple, list)) and len(value) == 2):
                raise Error("invalid value: {}={!r}".format(self.name, value))
            find, replace = value
            if not isinstance(replace, str):
                raise Error("invalid value: {}={!r}".format(self.name, value))
            allchars = find + replace
        else:
            allchars = find = value
        if not isinstance(find, RegexPattern):
            raise Error("invalid value: {}={!r}".format(self.name, value))
        pattern, delim = self.delimit(find, allchars)
        if self.replace:
            if delim in replace:
                replace = self.escape(replace, delim)
            pattern += replace + delim
        return pattern + self.repr_flags(find)


class VarArgs(Field):
    """Argument type that consumes a variable number of arguments

    :param name: Name of the list of consumed arguments.
    :param field: A field to be consumed a variable number of times.
    :param min: Minimum number of times to consume field (default is 1).
    :param placeholder:
    :param default: The default value if there are no arguments to consume.
    If this is callable it will be called with no arguments to create a value
    each time the default value is needed.
    PROPOSED: `field` may be a list of fields in which case the result of this
    VarArgs field will be a list of dicts. Are they all required?
    """

    def __init__(self, name, field, *, min=1, placeholder=None, **kw):
        kw.setdefault('default', list)
        self.args = [name, field]
        self.kwargs = {"min": min, "placeholder": placeholder}
        self.kwargs.update(kw)
        super().__init__(name, **kw)
        self.field = field
        self.min = min
        self.placeholder = placeholder

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default
    @default.setter
    def default(self, value):
        self._default = value

    def __str__(self):
        if self.placeholder is None:
            return "{} ...".format(self.field.name)
        return self.placeholder

    def with_context(self, *args, **kw):
        field = self.field.with_context(*args, **kw)
        return VarArgs(self.name, field, **self.kwargs)

    def consume(self, text, index):
        values = []
        if index >= len(text):
            value, index = self.field.consume(text, index)
            values.append(value)
        else:
            while index < len(text):
                value, index = self.field.consume(text, index)
                values.append(value)
        if len(values) < self.min:
            raise Error("not enough arguments (found {}, expected {})".format(
                        len(values), self.min))
        return values, index

    def get_placeholder(self, arg):
        text = arg.text
        index = arg.start
        start = None
        while index != start:
            start = index
            sub = Arg(self.field, text, index, arg.preceding)
            if sub.could_consume_more:
                value = sub.get_placeholder()
                if value is not None or index > len(text):
                    break
            if sub.errors:
                return None
            index = sub.end
        if value is None:
            return value
        placeholder = "..." if self.placeholder is None else self.placeholder
        return "{} {}".format(value, placeholder)

    def get_completions(self, arg):
        index = arg.start
        while True:
            sub = Arg(self.field, arg.text, index, arg.preceding)
            if sub.could_consume_more:
                return sub.get_completions()
            if sub.errors or sub.end == index:
                break
            index = sub.end
        return []

    def arg_string(self, value):
        return " ".join(self.field.arg_string(v) for v in value)


class SubParser(Field):
    """Dispatch to a named group of sub arguments

    The first argument consumed by this SubParser is used to lookup a
    SubArgs instance by name, and remaining arguments are parsed using
    the SubArgs.

    :param name: Name of sub-parser result.
    :param *subargs: One or more SubArgs objects containing more
    arguments to be parsed.
    """

    def __init__(self, name, *subargs):
        self.args = (name,) + subargs
        super(SubParser, self).__init__(name)
        self.subargs = {p.name: p for p in subargs}

    def with_context(self, *args, **kw):
        subs = [a.with_context(*args, **kw)
                for a in self.args[1:]
                if a.is_enabled(*args, **kw)]
        return SubParser(self.name, *subs)

    def consume(self, text, index):
        """Consume arguments based on the name of the first argument

        :returns: ((subparser, <consumed argument options>), <index>)
        :raises: ParserError, ArgumentError with sub-errors
        """
        name, end = Arg.consume_token(text, index)
        if not name:
            return self.default, end
        sub = self.subargs.get(name)
        if sub is None:
            names = [n for n in self.subargs if n.startswith(name)]
            if len(names) != 1:
                if len(names) > 1:
                    msg = "{!r} is ambiguous: {}".format(
                            name, ", ".join(sorted(self.subargs)))
                else:
                    msg = "{!r} does not match any of: {}".format(
                            name, ", ".join(sorted(self.subargs)))
                    end = index + len(name)
                raise ParseError(msg, self, index, end)
            sub = self.subargs[names[0]]
        opts, index = sub.parse(text, end)
        return (sub, opts), index

    def get_placeholder(self, arg):
        if not arg:
            return "{} ...".format(self)
        text = arg.text
        name, end = arg.consume_token()
        space_after_name = end < len(text) or text[arg.start:end].endswith(" ")
        if name is None:
            if space_after_name:
                return str(self)
            return "{} ...".format(self)
        sub = self.subargs.get(name)
        if sub is None:
            names = [n for n in self.subargs if n.startswith(name)]
            if not names:
                return None
            if len(names) > 1:
                if space_after_name:
                    return None
                return "..."
            sub = self.subargs[names[0]]
            placeholder = names[0][len(name):]
        else:
            placeholder = ""
        values = [] if space_after_name else [placeholder]
        values.append(sub.parser.get_placeholder(text, end))
        return " ".join(values)

    def get_completions(self, arg):
        text = arg.text
        name, end = arg.consume_token()
        if name is None:
            assert end >= len(text), (arg, text)
            return sorted(self.subargs)
        if end > len(text):
            # there is no space after name
            return [w for w in sorted(self.subargs) if w.startswith(name)]
        sub = self.subargs.get(name)
        if sub is None:
            names = [n for n in self.subargs if n.startswith(name)]
            if len(names) != 1:
                return []
            sub = self.subargs[names[0]]
        return sub.parser.get_completions(text, end)

    def arg_string(self, value):
        sub, opts = value
        return sub.name + " " + sub.parser.arg_string(opts, strip=False)


class SubArgs(object):
    """Arguments and data for SubParser"""

    def __init__(self, name, *argspec, is_enabled=None, **data):
        self.name = name
        self.data = data
        self._is_enabled = is_enabled
        self.parser = CommandParser(*argspec)

    def is_enabled(self, editor):
        if self._is_enabled is not None:
            return self._is_enabled(editor)
        return editor is not None and editor.text_view is not None

    def with_context(self, *args, **kw):
        sub = super(SubArgs, SubArgs).__new__(SubArgs)
        sub.name = self.name
        sub.data = self.data
        sub._is_enabled = self._is_enabled
        sub.parser = self.parser.with_context(*args, **kw)
        return sub

    def parse(self, text, index):
        args = Options()
        errors = []
        for arg in self.parser.tokenize(text, index, args):
            if arg.field is None:
                index = arg.start
                break
            if arg.errors:
                errors.extend(arg.errors)
            else:
                index = arg.end
        if errors:
            msg = 'invalid arguments: {}'.format(text)
            raise ArgumentError(msg, args, errors, index)
        return args, index

    def __repr__(self):
        args = [repr(self.name)]
        args.extend(repr(a) for a in self.parser.argspec)
        if self._is_enabled is not None:
            args.append("is_enabled={!r}".format(self._is_enabled))
        args.extend("{}={!r}".format(*kv) for kv in sorted(self.data.items()))
        return "{}({})".format(type(self).__name__, ", ".join(args))


class Conditional(Field):

    def __init__(self, is_enabled, field, editor=None, **kw):
        default = kw.setdefault('default', field.default)
        self.args = [is_enabled, field, default]
        super().__init__(field.name, default)
        self.is_enabled = is_enabled
        self.field = field
        self.editor = editor

    def with_context(self, editor):
        field = self.field.with_context(editor)
        return type(self)(self.is_enabled, field, editor, default=self.default)

    def consume(self, text, index):
        return self.field.consume(text, index)

    def value_of(self, consumed, arg):
        if not self.is_enabled(arg):
            raise SkipField(self.default)
        return self.field.value_of(consumed, arg)

    def get_placeholder(self, arg):
        return self.field.get_placeholder(arg)

    def get_completions(self, arg):
        return self.field.get_completions(arg)

    def arg_string(self, value):
        return self.field.arg_string(value)


class Options(object):
    """Parsed argument container

    Options are stored as attributes. Attribute names containing a double-
    underscore (__) are considered to be private and are excluded from
    operations that affect option values.
    """

    # DEFAULTS = <dict of defaults> # optional attribute for subclasses

    def __init__(self, **opts):
        if hasattr(self, "DEFAULTS"):
            for name, value in self.DEFAULTS.items():
                if name not in opts:
                    setattr(self, name, value)
        for name, value in list(opts.items()):
            setattr(self, name, value)

    def __eq__(self, other):
        return issubclass(type(other), Options) and dict(self) == dict(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        obj = Options().__dict__
        return ((k, v)
            for k, v in self.__dict__.items()
            if k not in obj and "__" not in k)

    def __len__(self):
        return len(list(self.__iter__()))

    def __repr__(self):
        def line_repr(obj):
            rep = repr(obj)
            if '\n' in rep:
                rep = rep.replace('\n', ' ')
            return rep
        vars = ['{}={}'.format(k, line_repr(v)) for k, v in self]
        return '{}({})'.format(type(self).__name__, ', '.join(vars))


class CompleteWord(str):

    def __new__(cls, _value="", get_delimiter=None, start=None, **kw):
        obj = super(CompleteWord, cls).__new__(cls, _value)
        if isinstance(_value, CompleteWord):
            if get_delimiter is None:
                get_delimiter = _value.get_delimiter
            if start is None:
                start = _value.start
            for key, value in _value.__dict__.items():
                if not key.startswith("_") and key not in kw:
                    setattr(obj, key, value)
        obj.get_delimiter = get_delimiter or (lambda:" ")
        obj.start = start
        obj.__dict__.update(kw)
        return obj

    def complete(self):
        return self + self.get_delimiter()


class CompletionsList(list):

    __slots__ = ["title"]

    def __init__(self, *args, title=None):
        super().__init__(*args)
        self.title = title


class Error(Exception):

    def __str__(self):
        return self.args[0]

    def __eq__(self, other):
        if not issubclass(type(other), type(self)):
            return False
        return self.args == other.args

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return id(self)


class ArgumentError(Error):

    def __str__(self):
        ext = ""
        if self.errors:
            ext = "\n" + "\n".join(str(err) for err in self.errors)
        return self.args[0] + ext

    @property
    def options(self):
        return self.args[1]

    @property
    def errors(self):
        return self.args[2]

    @property
    def parse_index(self):
        return self.args[3]


class ParseError(Error):

    @property
    def arg(self):
        return self.args[1]

    @property
    def error_index(self):
        return self.args[2]

    @property
    def parse_index(self):
        return self.args[3]


class SkipField(Error):

    @property
    def value(self):
        return self.args[0]
