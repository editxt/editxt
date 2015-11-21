# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: kotlin.js
name = 'Kotlin'
file_patterns = ['*.kotlin']

literal = ['true', 'false', 'null']

keyword = [
    'val',
    'var',
    'get',
    'set',
    'class',
    'trait',
    'object',
    'open',
    'private',
    'protected',
    'public',
    'final',
    'enum',
    'if',
    'else',
    'do',
    'while',
    'for',
    'when',
    'break',
    'continue',
    'throw',
    'try',
    'catch',
    'finally',
    'import',
    'package',
    'is',
    'as',
    'in',
    'return',
    'fun',
    'override',
    'default',
    'companion',
    'reified',
    'inline',
    'volatile',
    'transient',
    'native',
    'Byte',
    'Short',
    'Char',
    'Int',
    'Long',
    'Boolean',
    'Float',
    'Double',
    'Void',
    'Unit',
    'Nothing',
]

doctag = [RE(r"@[A-Za-z]+")]

doctag0 = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag), ('doctag', doctag0)]

class comment0:
    default_text = DELIMITER
    word_groups = [('doctag', doctag0)]
comment0.__name__ = 'comment'

title = [RE(r"[a-zA-Z_]\w*")]

class _group3:
    default_text = DELIMITER
    word_groups = [('title', title)]

keyword0 = ['reified']

class type:
    default_text = DELIMITER
    word_groups = [('keyword', keyword0)]

class params:
    default_text = DELIMITER
    word_groups = [('keyword', keyword)]
    delimited_ranges = [('type', RE(r":\s*"), [RE(r"(?=\s*[=\)])")])]

class function:
    default_text = DELIMITER
    word_groups = [('keyword', keyword)]
    delimited_ranges = [
        ('_group3', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B|\b")], _group3),
        ('type', RE(r"<"), [RE(r">")], type),
        ('params', RE(r"\("), [RE(r"\)")], params),
        ('comment', RE(r"//"), [RE(r"$")], comment0),
        ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ]

keyword1 = ['class', 'trait']

class class0:
    default_text = DELIMITER
    word_groups = [('keyword', keyword1), ('title', title)]
    delimited_ranges = [
        ('type', RE(r"<"), [RE(r"(?=>)")]),
        ('type', RE(r"[,:]\s*"), [RE(r"(?=[<\(,]|$)")]),
    ]
class0.__name__ = 'class'

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

word_groups = [('literal', literal), ('keyword', keyword), ('number', number)]

delimited_ranges = [
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    ('comment', RE(r"//"), [RE(r"$")], comment0),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('type', RE(r"(?=<)"), [RE(r">")]),
    ('function', RE(r"(?=\b(fun))"), [RE(r"(?=[(]|$)")], function),
    ('class', RE(r"\b(class|trait)"), [RE(r"(?=[:\{(]|$)")], class0),
    ('variable', RE(r"\b(var|val)"), [RE(r"(?=\s*[=:$])")]),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('meta', RE(r"^#!/usr/bin/env"), [RE(r"$")]),
]
