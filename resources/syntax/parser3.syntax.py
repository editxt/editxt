# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: parser3.js
name = 'Parser3'
file_patterns = ['*.parser3']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class comment0:
    default_text_color = DELIMITER
    rules = [
        ('comment', RE(r"{"), [RE(r"}")], comment),
        # ('contains', 0, 'contains', 0) {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

meta = [RE(r"^@(?:BASE|USE|CLASS|OPTIONS)$")]

title = [RE(r"@[\w\-]+\[[\w^;\-]*\](?:\[[\w^;\-]*\])?(?:.*)$")]

variable = [RE(r"\$\{?[\w\-\.\:]+\}?")]

keyword = [RE(r"\^[\w\-\.\:]+")]

number = [RE(r"\^#[0-9a-fA-F]+")]

number0 = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('comment', RE(r"^#"), [RE(r"$")], comment),
    ('comment', RE(r"\^rem{"), [RE(r"}")], comment0),
    ('meta', meta),
    ('title', title),
    ('variable', variable),
    ('keyword', keyword),
    ('number', number),
    ('number', number0),
]
