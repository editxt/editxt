# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: ceylon.js
name = 'Ceylon'
file_patterns = ['*.ceylon']

meta = ['doc', 'by', 'license', 'see', 'throws', 'tagged']

keyword = [
    'assembly',
    'module',
    'package',
    'import',
    'alias',
    'class',
    'interface',
    'object',
    'given',
    'value',
    'assign',
    'void',
    'function',
    'new',
    'of',
    'extends',
    'satisfies',
    'abstracts',
    'in',
    'out',
    'return',
    'break',
    'continue',
    'throw',
    'assert',
    'dynamic',
    'if',
    'else',
    'switch',
    'case',
    'for',
    'while',
    'try',
    'catch',
    'finally',
    'then',
    'let',
    'this',
    'outer',
    'super',
    'is',
    'exists',
    'nonempty',
    'shared',
    'abstract',
    'formal',
    'default',
    'actual',
    'variable',
    'late',
    'native',
    'deprecatedfinal',
    'sealed',
    'annotation',
    'suppressWarnings',
    'small',
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

meta0 = [RE(r"@[a-z]\w*(?:\:\"[^\"]*\")?")]

keyword0 = [
    'assembly',
    'module',
    'package',
    'import',
    'alias',
    'class',
    'interface',
    'object',
    'given',
    'value',
    'assign',
    'void',
    'function',
    'new',
    'of',
    'extends',
    'satisfies',
    'abstracts',
    'in',
    'out',
    'return',
    'break',
    'continue',
    'throw',
    'assert',
    'dynamic',
    'if',
    'else',
    'switch',
    'case',
    'for',
    'while',
    'try',
    'catch',
    'finally',
    'then',
    'let',
    'this',
    'outer',
    'super',
    'is',
    'exists',
    'nonempty',
]

number = [
    RE(r"#[0-9a-fA-F_]+|\$[01_]+|[0-9_]+(?:\.[0-9_](?:[eE][+-]?\d+)?)?[kMGTPmunpf]?"),
]

class subst:
    default_text = DELIMITER
    word_groups = [('keyword', keyword0), ('number', number)]
    delimited_ranges = [
        ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('string', RE(r"'"), [RE(r"'")]),
    ]

class string:
    default_text = DELIMITER
    delimited_ranges = [('subst', RE(r"``"), [RE(r"(?=``)")], subst)]

word_groups = [
    ('meta', meta),
    ('keyword', keyword),
    ('meta', meta0),
    ('number', number),
]

delimited_ranges = [
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"'")]),
]
