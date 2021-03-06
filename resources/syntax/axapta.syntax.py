# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: axapta.js
name = 'Axapta'
file_patterns = ['*.axapta']

keyword = """
    false int abstract private char boolean static null if for true
    while long throw finally protected final return void enum else break
    new catch byte super case short default double public try this
    switch continue reverse firstfast firstonly forupdate nofetch sum
    avg minof maxof count order group by asc desc index hint like
    dispaly edit client server ttsbegin ttscommit str real date
    container anytype common div mod
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class _class0:
    default_text_color = DELIMITER
    rules = [('_class', [RE(r"{")])]
_class0.__name__ = '_class'

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class', 'interface']),
        ('_group1', RE(r"\b(?:extends|implements)"), [RE(r"(?={)")]),
        ('title', [RE(r"[a-zA-Z_]\w*")]),
    ]
class0.__name__ = 'class'

rules = [
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('meta', RE(r"#"), [RE(r"$")]),
    ('class', RE(r"\b(?:class|interface)"), [_class0], class0),
]
