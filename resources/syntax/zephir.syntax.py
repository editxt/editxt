# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: zephir.js
name = 'Zephir'
file_patterns = ['*.zephir', '*.zep']

flags = re.IGNORECASE | re.MULTILINE

keyword = [
    'and',
    'include_once',
    'list',
    'abstract',
    'global',
    'private',
    'echo',
    'interface',
    'as',
    'static',
    'endswitch',
    'array',
    'null',
    'if',
    'endwhile',
    'or',
    'const',
    'for',
    'endforeach',
    'self',
    'var',
    'let',
    'while',
    'isset',
    'public',
    'protected',
    'exit',
    'foreach',
    'throw',
    'elseif',
    'include',
    '__FILE__',
    'empty',
    'require_once',
    'do',
    'xor',
    'return',
    'parent',
    'clone',
    'use',
    '__CLASS__',
    '__LINE__',
    'else',
    'break',
    'print',
    'eval',
    'new',
    'catch',
    '__METHOD__',
    'case',
    'exception',
    'default',
    'die',
    'require',
    '__FUNCTION__',
    'enddeclare',
    'final',
    'try',
    'switch',
    'continue',
    'endfor',
    'endif',
    'declare',
    'unset',
    'true',
    'false',
    'trait',
    'goto',
    'instanceof',
    'insteadof',
    '__DIR__',
    '__NAMESPACE__',
    'yield',
    'finally',
    'int',
    'uint',
    'long',
    'ulong',
    'char',
    'uchar',
    'double',
    'float',
    'bool',
    'boolean',
    'stringlikely',
    'unlikely',
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

doctag0 = [RE(r"@[A-Za-z]+")]

class comment1:
    default_text = DELIMITER
    rules = [
        ('doctag', doctag0),
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment1.__name__ = 'comment'

keyword0 = ['__halt_compiler']

class comment2:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment2.__name__ = 'comment'

keyword1 = ['function']

title = [RE(r"[a-zA-Z_]\w*")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

number = [RE(r"\b(0b[01]+)")]

number0 = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

class params:
    default_text = DELIMITER
    rules = [
        ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
        ('string', RE(r"b\""), [RE(r"\"")], string),
        ('string', RE(r"b'"), [RE(r"'")], string),
        ('string', RE(r"'"), [RE(r"'")], string),
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('number', number),
        ('number', number0),
    ]

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword1),
        ('title', title),
        ('params', RE(r"\("), [RE(r"\)")], params),
    ]

keyword2 = ['class', 'interface']

class class0:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword2),
        ('_group1', RE(r"\b(extends|implements)"), [RE(r"\B|\b")]),
        None,  # ('title', title),
    ]
class0.__name__ = 'class'

keyword3 = ['namespace']

class _group2:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword3),
        None,  # ('title', title),
    ]

keyword4 = ['use']

class _group3:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword4),
        None,  # ('title', title),
    ]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"#"), [RE(r"$")], comment0),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment1),
    ('comment', RE(r"__halt_compiler.+?;"), [RE(r"")], comment2),
    ('string', RE(r"<<<['\"]?\w+['\"]?$"), [RE(r"^\w+;")]),
    ('function', RE(r"\b(function)"), [RE(r"(?=[;{])")], function),
    ('class', RE(r"\b(class|interface)"), [RE(r"(?={)")], class0),
    ('_group2', RE(r"\b(namespace)"), [RE(r";")], _group2),
    ('_group3', RE(r"\b(use)"), [RE(r";")], _group3),
    None,  # params.rules[2],
    None,  # ('number', number0),
]

class0.rules[2] = ('title', title)
_group2.rules[1] = ('title', title)
_group3.rules[1] = ('title', title)
rules[10] = params.rules[2]
rules[11] = ('number', number0)

# TODO merge "word_groups" and "delimited_ranges" into "rules" in editxt.syntax
assert "__obj" not in globals()
assert "__fixup" not in globals()
def __fixup(obj):
    groups = []
    ranges = []
    rules = getattr(obj, "rules", [])
    for i, rng in reversed(list(enumerate(rules))):
        if len(rng) == 2:
            groups.append(rng)
        else:
            assert len(rng) > 2, rng
            ranges.append(rng)
    return groups, ranges

class __obj:
    rules = globals().get("rules", [])
word_groups, delimited_ranges = __fixup(__obj)

for __obj in globals().values():
    if hasattr(__obj, "rules"):
        __obj.word_groups, __obj.delimited_ranges = __fixup(__obj)

del __obj, __fixup
