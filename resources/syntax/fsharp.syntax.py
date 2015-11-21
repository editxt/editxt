# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: fsharp.js
name = 'F#'
file_patterns = ['*.fsharp', '*.fs']

keyword = [
    'abstract',
    'and',
    'as',
    'assert',
    'base',
    'begin',
    'class',
    'default',
    'delegate',
    'do',
    'done',
    'downcast',
    'downto',
    'elif',
    'else',
    'end',
    'exception',
    'extern',
    'false',
    'finally',
    'for',
    'fun',
    'function',
    'global',
    'if',
    'in',
    'inherit',
    'inline',
    'interface',
    'internal',
    'lazy',
    'let',
    'match',
    'member',
    'module',
    'mutable',
    'namespace',
    'new',
    'null',
    'of',
    'open',
    'or',
    'override',
    'private',
    'public',
    'rec',
    'return',
    'sig',
    'static',
    'struct',
    'then',
    'to',
    'true',
    'try',
    'type',
    'upcast',
    'use',
    'val',
    'void',
    'when',
    'while',
    'with',
    'yield',
]

keyword0 = [RE(r"\b(yield|return|let|do)!")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

keyword1 = ['type']

title = [RE(r"[a-zA-Z_]\w*")]

title0 = [RE(r"'[a-zA-Z0-9_]+")]

class _group2:
    default_text = DELIMITER
    word_groups = [('title', title0)]

class class0:
    default_text = DELIMITER
    word_groups = [('keyword', keyword1), ('title', title)]
    delimited_ranges = [('_group2', RE(r"<"), [RE(r">")], _group2)]
class0.__name__ = 'class'

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

word_groups = [('keyword', keyword), ('keyword', keyword0), ('number', number)]

delimited_ranges = [
    ('string', RE(r"@\""), [RE(r"\"")]),
    ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
    ('comment', RE(r"\(\*"), [RE(r"\*\)")], comment),
    ('class', RE(r"\b(type)"), [RE(r"(?=\(|=|$)")], class0),
    ('meta', RE(r"\[<"), [RE(r">\]")]),
    ('symbol', RE(r"\B('[A-Za-z])\b"), [RE(r"\B|\b")]),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('string', RE(r"\""), [RE(r"\"")]),
]
