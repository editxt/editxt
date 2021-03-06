# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: groovy.js
name = 'Groovy'
file_patterns = ['*.groovy']

keyword = """
    byte short char int long boolean float double void def as in assert
    trait super this abstract static volatile transient public private
    protected synchronized final class interface enum if else for while
    switch case break default continue throw throws try catch finally
    implements extends new import package return instanceof
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': '\\w+@', 'type': 'RegExp'}, 'relevance': 0},
        ('doctag', [RE(r"@[A-Za-z]+")]),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class comment1:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]
comment1.__name__ = 'comment'

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string2:
    default_text_color = DELIMITER
    rules = [operator_escape]
string2.__name__ = 'string'

class regexp:
    default_text_color = DELIMITER
    rules = [operator_escape]

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class', 'interface', 'trait', 'enum']),
        ('_group2', RE(r"\b(?:extends|implements)"), [RE(r"(?={)")]),
        ('title', [RE(r"[a-zA-Z_]\w*")]),
    ]
class0.__name__ = 'class'

number0 = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('keyword', keyword),
    ('literal', ['true', 'false', 'null']),
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    ('comment', RE(r"//"), [RE(r"$")], comment1),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment1),
    ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
    ('string', RE(r"'''"), [RE(r"'''")]),
    ('string', RE(r"\$/"), [RE(r"/\$")]),
    ('string', RE(r"'"), [RE(r"'")], string2),
    ('regexp', RE(r"~?\/[^\/\n]+\/"), [RE(r"\B|\b")], regexp),
    ('string', RE(r"\""), [RE(r"\"")], string2),
    ('meta', RE(r"^#!/usr/bin/env"), [RE(r"$")]),
    ('number', [RE(r"\b(?:0b[01]+)")]),
    ('class', RE(r"\b(?:class|interface|trait|enum)"), [RE(r"{")], class0),
    ('number', number0),
    ('meta', [RE(r"@[A-Za-z]+")]),
    ('string', [RE(r"[^\?]{0}[A-Za-z0-9_$]+ *:")]),
    ('_group3', RE(r"\?"), [RE(r"\:")]),
    ('symbol', [RE(r"^\s*[A-Za-z0-9_$]+:")]),
]
