# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: zephir.js
name = 'Zephir'
file_patterns = ['*.zephir', '*.zep']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    and include_once list abstract global private echo interface as
    static endswitch array null if endwhile or const for endforeach self
    var let while isset public protected exit foreach throw elseif
    include __FILE__ empty require_once do xor return parent clone use
    __CLASS__ __LINE__ else break print eval new catch __METHOD__ case
    exception default die require __FUNCTION__ enddeclare final try
    switch continue endfor endif declare unset true false trait goto
    instanceof insteadof __DIR__ __NAMESPACE__ yield finally int uint
    long ulong char uchar double float bool boolean stringlikely
    unlikely
    """.split()

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

doctag0 = [RE(r"@[A-Za-z]+")]

class comment0:
    default_text_color = DELIMITER
    rules = [
        ('doctag', doctag0),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

keyword0 = ['__halt_compiler']

class comment1:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword0),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment1.__name__ = 'comment'

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _function:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r"[;{]")])]

keyword1 = ['function']

title = [RE(r"[a-zA-Z_]\w*")]

number = [RE(r"\b(?:0b[01]+)")]

number0 = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class params:
    default_text_color = DELIMITER
    rules = [
        ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
        ('string', RE(r"b\""), [RE(r"\"")], string),
        ('string', RE(r"b'"), [RE(r"'")], string),
        ('string', RE(r"'"), [RE(r"'")], string),
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('number', number),
        ('number', number0),
    ]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword1),
        ('title', title),
        ('params', RE(r"\("), [RE(r"\)")], params),
    ]

class _class:
    default_text_color = DELIMITER
    rules = [('_class', [RE(r"{")])]

keyword2 = ['class', 'interface']

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword2),
        ('_group2', RE(r"\b(?:extends|implements)"), [RE(r"\B\b")]),
        ('title', title),
    ]
class0.__name__ = 'class'

keyword3 = ['namespace']

class _group0:
    default_text_color = DELIMITER
    rules = [('keyword', keyword3), ('title', title)]

keyword4 = ['use']

class _group1:
    default_text_color = DELIMITER
    rules = [('keyword', keyword4), ('title', title)]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('comment', RE(r"__halt_compiler.+?;"), [RE(r"\B\b")], comment1),
    ('string', RE(r"<<<['\"]?\w+['\"]?$"), [RE(r"^\w+;")], string),
    # ignore {'begin': {'pattern': '(::|->)+[a-zA-Z_\\x7f-\\xff][a-zA-Z0-9_\\x7f-\\xff]*', 'type': 'RegExp'}},
    ('function', RE(r"\b(?:function)"), [_function], function),
    ('class', RE(r"\b(?:class|interface)"), [_class], class0),
    ('_group0', RE(r"\b(?:namespace)"), [RE(r";")], _group0),
    ('_group1', RE(r"\b(?:use)"), [RE(r";")], _group1),
    # ignore {'begin': '=>'},
    params.rules[1],
    params.rules[2],
    params.rules[3],
    params.rules[4],
    params.rules[5],
    params.rules[6],
]
