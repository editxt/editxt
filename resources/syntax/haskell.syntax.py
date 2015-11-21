# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: haskell.js
name = 'Haskell'
file_patterns = ['*.haskell', '*.hs']

keyword = [
    'let',
    'in',
    'if',
    'then',
    'else',
    'case',
    'of',
    'where',
    'do',
    'module',
    'import',
    'hiding',
    'qualified',
    'type',
    'data',
    'newtype',
    'deriving',
    'class',
    'instance',
    'as',
    'default',
    'infix',
    'infixl',
    'infixr',
    'foreign',
    'export',
    'ccall',
    'stdcall',
    'cplusplus',
    'jvm',
    'dotnet',
    'safe',
    'unsafe',
    'family',
    'forall',
    'mdo',
    'proc',
    'rec',
]

keyword0 = ['module', 'where']

type = [RE(r"\b[A-Z][\w]*(\((\.\.|,|\w+)\))?")]

title = [RE(r"[_a-z][\w']*")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

class _group1:
    default_text = DELIMITER
    word_groups = [('type', type), ('title', title)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('meta', RE(r"^#"), [RE(r"$")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class _group0:
    default_text = DELIMITER
    word_groups = [('keyword', keyword0)]
    delimited_ranges = [
        ('_group1', RE(r"\("), [RE(r"\)")], _group1),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

keyword1 = ['import', 'qualified', 'as', 'hiding']

class _group7:
    default_text = DELIMITER
    word_groups = [('type', type), ('title', title)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('meta', RE(r"^#"), [RE(r"$")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class _group6:
    default_text = DELIMITER
    word_groups = [('keyword', keyword1)]
    delimited_ranges = [
        ('_group7', RE(r"\("), [RE(r"\)")], _group7),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

keyword2 = ['class', 'family', 'instance', 'where']

type0 = [RE(r"\b[A-Z][\w']*")]

class _group12:
    default_text = DELIMITER
    word_groups = [('type', type), ('title', title)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('meta', RE(r"^#"), [RE(r"$")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class class0:
    default_text = DELIMITER
    word_groups = [('keyword', keyword2), ('type', type0)]
    delimited_ranges = [
        ('_group12', RE(r"\("), [RE(r"\)")], _group12),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]
class0.__name__ = 'class'

keyword3 = ['data', 'family', 'type', 'newtype', 'deriving']

class _group17:
    default_text = DELIMITER
    word_groups = [('type', type), ('title', title)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('meta', RE(r"^#"), [RE(r"$")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class _group20:
    default_text = DELIMITER
    word_groups = [('type', type), ('title', title)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('meta', RE(r"^#"), [RE(r"$")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class class1:
    default_text = DELIMITER
    word_groups = [('keyword', keyword3), ('type', type0)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('_group17', RE(r"\("), [RE(r"\)")], _group17),
        ('_group20', RE(r"{"), [RE(r"}")], _group20),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]
class1.__name__ = 'class'

keyword4 = ['default']

class _group26:
    default_text = DELIMITER
    word_groups = [('type', type), ('title', title)]
    delimited_ranges = [
        ('meta', RE(r"{-#"), [RE(r"#-}")]),
        ('meta', RE(r"^#"), [RE(r"$")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class _group25:
    default_text = DELIMITER
    word_groups = [('keyword', keyword4), ('type', type0)]
    delimited_ranges = [
        ('_group26', RE(r"\("), [RE(r"\)")], _group26),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

keyword5 = ['infix', 'infixl', 'infixr']

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

class _group31:
    default_text = DELIMITER
    word_groups = [('keyword', keyword5), ('number', number)]
    delimited_ranges = [
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

keyword6 = [
    'foreign',
    'import',
    'export',
    'ccall',
    'stdcall',
    'cplusplus',
    'jvm',
    'dotnet',
    'safe',
    'unsafe',
]

class _group34:
    default_text = DELIMITER
    word_groups = [('keyword', keyword6), ('type', type0)]
    delimited_ranges = [
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

title0 = [RE(r"^[_a-z][\w']*")]

word_groups = [
    ('keyword', keyword),
    ('number', number),
    ('type', type0),
    ('title', title0),
]

delimited_ranges = [
    ('_group0', RE(r"\b(module)"), [RE(r"where")], _group0),
    ('_group6', RE(r"\bimport\b"), [RE(r"$")], _group6),
    ('class', RE(r"^(\s*)?(class|instance)\b"), [RE(r"where")], class0),
    ('class', RE(r"\b(data|(new)?type)\b"), [RE(r"$")], class1),
    ('_group25', RE(r"\b(default)"), [RE(r"$")], _group25),
    ('_group31', RE(r"\b(infix|infixl|infixr)"), [RE(r"$")], _group31),
    ('_group34', RE(r"\bforeign\b"), [RE(r"$")], _group34),
    ('meta', RE(r"#!\/usr\/bin\/env runhaskell"), [RE(r"$")]),
    ('meta', RE(r"{-#"), [RE(r"#-}")]),
    ('meta', RE(r"^#"), [RE(r"$")]),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('comment', RE(r"--"), [RE(r"$")], comment),
    ('comment', RE(r"{-"), [RE(r"-}")], comment),
]
