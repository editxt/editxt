# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: go.js
name = 'Go'
file_patterns = ['*.go', '*.golang']

literal = ['true', 'false', 'iota', 'nil']

keyword = [
    'break',
    'default',
    'func',
    'interface',
    'select',
    'case',
    'map',
    'struct',
    'chan',
    'else',
    'goto',
    'package',
    'switch',
    'const',
    'fallthrough',
    'if',
    'range',
    'type',
    'continue',
    'for',
    'import',
    'return',
    'var',
    'go',
    'defer',
    'bool',
    'byte',
    'complex64',
    'complex128',
    'float32',
    'float64',
    'int8',
    'int16',
    'int32',
    'int64',
    'string',
    'uint8',
    'uint16',
    'uint32',
    'uint64',
    'int',
    'uint',
    'uintptr',
    'rune',
]

built_in = [
    'append',
    'cap',
    'close',
    'complex',
    'copy',
    'imag',
    'len',
    'make',
    'new',
    'panic',
    'print',
    'println',
    'real',
    'recover',
    'delete',
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

number = [
    RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)[dflsi]?"),
]

number0 = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

word_groups = [
    ('literal', literal),
    ('keyword', keyword),
    ('built_in', built_in),
    ('number', number),
    ('number', number0),
]

delimited_ranges = [
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('string', RE(r"'"), [RE(r"[^\\]'")]),
    ('string', RE(r"`"), [RE(r"`")]),
]
