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

    def parse(self, text, index=0):
        """Parse arguments from the given text

        :param text: Argument string.
        :param index: Start parsing at this index in text.
        :raises: `ArgumentError` if the text string is invalid.
        :returns: `Options` object with argument values as attributes.
        """
        opts = Options()
        errors = []
        for arg in self.argspec:
            try:
                value, index = arg.consume(text, index) #, previous_errors=errors)
                errors = []
            except ParseError as err:
                errors.append(err)
                value = arg.default
            except ArgumentError as err:
                assert err.errors, "unexpected {!r}".format(err)
                errors.extend(err.errors)
                value = arg.default
            setattr(opts, arg.name, value)
        if errors:
            msg = 'invalid arguments: {}'.format(text)
            raise ArgumentError(msg, opts, errors, index)
        if index < len(text):
            msg = 'unexpected argument(s): ' + text[index:]
            raise ArgumentError(msg, opts, errors, index)
        return opts

    def default_options(self):
        return Options(**{arg.name: arg.default for arg in self.argspec})

    def get_placeholder(self, text):
        """Get placeholder string to follow the given command text

        :param text: Argument string.
        :returns: A string of placeholder text, which can be used as a
            hint about remaining arguments to be entered.
        """
        index = 0
        values = []
        for arg in self.argspec:
            value, next_index = arg.get_placeholder(text, index)
            if next_index is None:
                assert value is None, value
                continue
            index = next_index
            if value is not None:
                values.append(value)
        return " ".join(values)

    def get_completions(self, text):
        """Get completions for the given command text

        :param text: Argument string.
        :returns: A list of possible values to complete the command.
        """
        return self.parse_completions(text, 0)[0] or []

    def parse_completions(self, text, index):
        """Parse command text and return completions for the final argument

        :param text: Command text string.
        :param index: Position in text to begin parsing.
        :returns: ``(list_of_completions, end)`` where ``end`` is
        the index in ``text`` where parsing of this argument stopped.
        ``list_of_completions`` will be ``None`` if another argument
        (outside of this parser) could be parsed.
        """
        for arg in self.argspec:
            values, index = arg.parse_completions(text, index)
            if values is not None:
                return values, index
        # ??? None indicates an error (the last token could not be consumed) ???
        return None, index

    def arg_string(self, options, strip=True):
        """Compile command string from options

        :param options: Options object.
        :returns: Command argument string.
        :raises: Error
        """
        args = []
        for arg in self.argspec:
            try:
                value = getattr(options, arg.name)
            except AttributeError:
                raise Error("missing option: {}".format(arg.name))
            args.append(arg.arg_string(value))
        return " ".join(args).rstrip(" ") if strip else " ".join(args)


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

    def consume_token(self, text, index):
        """Helper method that consumes one token from text starting at index

        This consumes all text up to (including) the next space in the
        string. The returned token will not contain spaces. If the
        character at index is a space, then first element of the
        returned tuple will be `None` indicating that the argument
        should use its default value. This is meant to be called by
        subclasses; it is not part of the public interface.

        :param text: Argument string.
        :param index: Index from which to consume argument.
        :returns: A tuple `(<token string or None>, <index>)` where `index`
            is that following the last consumed character in `text`.
        """
        if index >= len(text):
            return None, index
        elif text[index] == ' ':
            return None, index + 1
        end = text.find(' ', index)
        if end < 0:
            token = text[index:]
            end = len(text)
        else:
            token = text[index:end]
            end += 1
        return token, end

    def parse_token(self, text, index):
        """Parse argument token from text starting at index

        :returns: ``(token, index, terminated)`` where ``token`` is
        text that would be consumed (possibly only after being completed
        with one of the items returned by ``get_completions``),
        ``index`` is the place in ``text`` to begin parsing the next
        token, and ``terminated`` is a boolean value indicating
        whether the token has been terminated, meaning that additional
        text beyond ``index`` would be a separate argument.
        :raises: See ``consume``.
        """
        value, end = self.consume(text, index)
        terminated = (
            index < end and         # token exists
            end <= len(text) and    # would not consume more
            text[end - 1] == " "    # space between tokens
        )
        return text[index:end], end, terminated

    def get_placeholder(self, text, index):
        """Get placeholder string for this argument

        If this argument matches the last argument in the given ``text``
        and it would consume any other character appended to ``text``,
        return an empty string ("") as the placeholder, which will cause
        following placeholders to be spaced away from the last character
        of ``text``.

        :param text: Argument string.
        :param index: Index in text to begin parsing.
        :returns: A two-tuple with the first item being a placeholder
        string (``None`` if an argument would have been consumed), and
        the second item being the index to resume parsing in text
        (``None`` if the argument was present but could be parsed).
        """
        if index >= len(text):
            return str(self), index
        try:
            token, index, terminated = self.parse_token(text, index)
        except ParseError as err:
            return None, None
        except ArgumentError as err:
            raise NotImplementedError # TODO
        return (None if terminated else ""), index

    def parse_completions(self, text, index):
        """See ``CommandParser.parse_completions`` for interface documentation
        """
        try:
            token, end, terminated = self.parse_token(text, index)
        except ParseError as err:
            token = text[index:err.parse_index]
            end = err.parse_index
            # HACK cannot really determine if terminated here:
            # case: "x " -> Int -> ParseError ... terminted=True
            # case: "' " -> String -> ParseError ... terminted=False
            if end >= len(text):
                values = self.get_completions(token)
                if values:
                    return values, err.parse_index
            return None, index
        except ArgumentError as err:
            raise NotImplementedError # TODO
        if terminated or end < len(text):
            # TODO what about Int(...).consume("x y", 0) ?
            values = None
        else:
            values = self.get_completions(token)
        return values, end

    def get_completions(self, token):
        """Get a list of possible completions for token

        :param text: Argument value prefix.
        :returns: A list of possible completions for given prefix.
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
        token, end = self.consume_token(text, index)
        if token is None:
            return self.default, end
        if token in self.mapping:
            return self.mapping[token], end
        names = ', '.join(n for n in self.names if n.startswith(token))
        if names:
            msg = '{!r} is ambiguous: {}'.format(token, names)
        else:
            names = ', '.join(self.names)
            msg = '{!r} does not match any of: {}'.format(token, names)
        raise ParseError(msg, self, index, end)

    def get_placeholder(self, text, index):
        if index >= len(text):
            return str(self), index
        token, end = self.consume_token(text, index)
        if not token:
            return None, end
        names = self.get_completions(token)
        if not names:
            placeholder = end = None
        elif text[index:end].endswith(" "):
            if len(names) == 1:
                placeholder = None
            else:
                placeholder = end = None
        elif len(names) == 1:
            placeholder = names[0][len(token):]
        else:
            placeholder = "..."
        return placeholder, end

    def get_completions(self, token):
        """List choice names that complete token"""
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
        token, end = self.consume_token(text, index)
        if token is None:
            return self.default, end
        try:
            return int(token), end
        except (ValueError, TypeError) as err:
            raise ParseError(str(err), self, index, end)

    def get_placeholder(self, text, index):
        if index >= len(text):
            if isinstance(self.default, int):
                return str(self.default), index
            return str(self), index
        return super(Int, self).get_placeholder(text, index)

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

    def consume(self, text, index):
        """Consume a string value

        :returns: (<string or default value>, <index>)
        """
        if index >= len(text):
            return self.default, index
        escapes = self.ESCAPES
        if text[index] not in ['"', "'"]:
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
                return ''.join(chars), len(text) # FIXME? should add one to index?
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
        if path.endswith((os.path.sep, "/")):
            raise ParseError("not a file: %s" % (path,), self, index, stop)
        if path.startswith('~'):
            path = os.path.expanduser(path)
        if os.path.isabs(path):
            return path, stop
        if self.path is None:
            raise Error("cannot make absolute path (no context): {}".format(path))
        return os.path.join(self.path, path), stop

    def get_completions(self, token):
        from os.path import exists, expanduser, isabs, isdir, join, sep, split
        if token == '~':
            return [CompleteWord('~/', (lambda:''), 1)]
        if token.startswith('~'):
            token = expanduser(token)
        if isabs(token):
            base = "/"
            path = token
        elif self.path is None:
            return []
        else:
            base = self.path
            path = join(base, token)
        root, name = split(path)
        assert len(base) <= len(root), (base, root)
        if not exists(root):
            return []
        assert len(sep) == 1, sep

        def delim(word):
            word = word.replace(' ', '\\ ')
            def get_delimiter():
                return "/" if isdir(join(root, word)) else " "
            return CompleteWord(word, get_delimiter, len(name))

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
            names.append(CompleteWord(name + "/", lambda:"", len(name)))
        return CompletionsList(names, title=user_path(root), selected_index=None)

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
        if index >= len(text):
            return self.default, index
        if text[index] not in self.DELIMITERS:
            msg = "invalid search pattern: {!r}".format(text[index:])
            raise ParseError(msg, self, index, len(text) - index)
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
        delim = text[index]
        chars, esc = [], 0
        i = -1
        for i, c in enumerate(text[index + 1:]):
            if esc:
                esc = 0
                chars.append(c)
                continue
            elif c == delim:
                return ''.join(chars), index + i + 2
            chars.append(c)
            if c == '\\':
                esc = 1
        if not esc:
            return ''.join(chars), index + i + 3
        token = ''.join(chars)
        msg = 'unterminated regex: {}{}'.format(delim, token)
        raise ParseError(msg, self, index, len(text))

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
        return value, index

    def get_placeholder(self, text, index):
        if index >= len(text):
            return str(self), index
        delim = text[index]
        try:
            value, end = self.consume(text, index, (None, None))
        except ParseError:
            return None, None
        if self.replace and value[1] is None:
            return delim * 2, end
        if end > len(text):
            return delim, end
        return (None if text[end - 1] == " " else ""), end

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
    PROPOSED: `field` may be a list of fields in which case the result of this
    VarArgs field will be a list of dicts. Are they all required?
    """

    def __init__(self, name, field, *, min=1, placeholder=None, **kw):
        self.args = [name, field]
        self.kwargs = {"min": min, "placeholder": placeholder}
        self.kwargs.update(kw)
        super().__init__(name, **kw)
        self.field = field
        self.min = min
        self.placeholder = placeholder

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

    def get_placeholder(self, text, index):
        parsed = 0
        prev_index = None
        while index != prev_index:
            prev_index = index
            value, index = self.field.get_placeholder(text, index)
            if index is None:
                return (None, (prev_index if parsed else index))
            if value is not None or index > len(text):
                break
            parsed += 1
        if value is None:
            return value, index
        placeholder = "..." if self.placeholder is None else self.placeholder
        return "{} {}".format(value, placeholder), index

    def parse_completions(self, text, index):
        while index < len(text):
            prev_index = index
            value, index = self.field.parse_completions(text, index)
            if index == prev_index or (index == len(text) and text[-1] != ' '):
                return value, index
        return self.field.parse_completions(text, index)

    def get_completions(self, token):
        return self.field.get_completions(token)

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
        name, end = self.consume_token(text, index)
        if not name:
            return self.default, end
        sub = self.subargs.get(name)
        if sub is None:
            names = [n for n in self.subargs if n.startswith(name)]
            if len(names) != 1:
                msg = "{!r} does not match any of: {}".format(
                        name, ", ".join(sorted(self.subargs)))
                raise ParseError(msg, self, index, end)
            sub = self.subargs[names[0]]
        try:
            opts = sub.parser.parse(text, end)
        except ArgumentError as err:
            if not err.errors:
                # we're finished, but there are unparsed arguments
                return (sub, err.options), err.parse_index
            raise
        return (sub, opts), len(text)

    def get_placeholder(self, text, index):
        if index >= len(text):
            return "{} ...".format(self), index
        name, end = self.consume_token(text, index)
        space_after_name = end < len(text) or text[index:end].endswith(" ")
        if name is None:
            if space_after_name:
                return self.default, end
            return "{} ...".format(self), end
        sub = self.subargs.get(name)
        if sub is None:
            names = [n for n in self.subargs if n.startswith(name)]
            if not names:
                return None, None
            if len(names) > 1:
                if space_after_name:
                    return None, None
                return "...", end
            sub = self.subargs[names[0]]
            placeholder = names[0][len(name):]
        else:
            placeholder = ""
        values = [] if space_after_name else [placeholder]
        index = end
        for arg in sub.parser.argspec:
            value, index = arg.get_placeholder(text, index)
            if index is None:
                return None, None
            if value is not None:
                values.append(value)
        return (" ".join(values) if values else None), index

    def parse_completions(self, text, index):
        """See ``CommandParser.parse_completions`` for interface documentation
        """
        name, end = self.consume_token(text, index)
        if name is None:
            if end < len(text) or text[index:end].endswith(" "):
                return None, end
            return sorted(self.subargs), end
        if len(name) == end - index:
            # there is no space after name
            return self.get_completions(name), end
        sub = self.subargs.get(name)
        if sub is None:
            names = [n for n in self.subargs if n.startswith(name)]
            if len(names) != 1:
                return [], len(text)
            sub = self.subargs[names[0]]
        return sub.parser.parse_completions(text, end)

    def get_completions(self, token):
        return [n for n in sorted(self.subargs) if n.startswith(token)]

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

    def __repr__(self):
        args = [repr(self.name)]
        args.extend(repr(a) for a in self.parser.argspec)
        if self._is_enabled is not None:
            args.append("is_enabled={!r}".format(self._is_enabled))
        args.extend("{}={!r}".format(*kv) for kv in sorted(self.data.items()))
        return "{}({})".format(type(self).__name__, ", ".join(args))


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

    __slots__ = ["get_delimiter", "overlap"]

    def __new__(cls, value="", get_delimiter=lambda:" ", overlap=None):
        obj = super(CompleteWord, cls).__new__(cls, value)
        obj.get_delimiter = get_delimiter
        obj.overlap = overlap
        return obj

    def complete(self):
        return self + self.get_delimiter()


class CompletionsList(list):

    __slots__ = ["title", "selected_index"]

    def __init__(self, *args, title=None, selected_index=0):
        super().__init__(*args)
        self.title = title
        self.selected_index = selected_index


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
