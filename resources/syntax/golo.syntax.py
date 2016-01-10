# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: golo.js
name = 'Golo'
file_patterns = ['*.golo']

keyword = """
    println readln print import module function local return let var
    while for foreach times in case when match with break continue
    augment augmentation each find filter reduce if then else otherwise
    try catch finally raise throw orIfNull DynamicObject DynamicVariable
    struct Observable map set vector list array
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('keyword', keyword),
    ('literal', ['true', 'false', 'null']),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('meta', [RE(r"@[A-Za-z]+")]),
]
