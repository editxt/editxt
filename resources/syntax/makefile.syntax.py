# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: makefile.js
name = 'Makefile'
file_patterns = ['*.makefile', '*.mk', '*.mak']

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class _group10:
    default_text_color = DELIMITER
    rules = [('_group1', RE(r"(?=^\w+\s*\W*=)"), [RE(r"\B|\b")])]
_group10.__name__ = '_group1'

class _group20:
    default_text_color = DELIMITER
    rules = [('_group2', _group10, [RE(r"\s*\W*=")])]
_group20.__name__ = '_group2'

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class variable:
    default_text_color = DELIMITER
    rules = [operator_escape]

variable0 = ('variable', RE(r"\$\("), [RE(r"\)")], variable)

class _group3:
    default_text_color = DELIMITER
    rules = [variable0]

class meta:
    default_text_color = DELIMITER
    rules = [('meta-keyword', ['.PHONY'])]

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

class _group4:
    default_text_color = DELIMITER
    rules = [('string', RE(r"\""), [RE(r"\"")], string), variable0]

rules = [
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('_group1', _group20, [RE(r"$")], _group3),
    ('section', [RE(r"^[\w]+:\s*$")]),
    ('meta', RE(r"^\.PHONY:"), [RE(r"$")], meta),
    ('_group4', RE(r"^\t+"), [RE(r"$")], _group4),
]
