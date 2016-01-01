# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: makefile.js
name = 'Makefile'
file_patterns = ['*.makefile', '*.mk', '*.mak']

section = [RE(r"^[\w]+:\s*$")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class _group0:
    default_text_color = DELIMITER
    rules = [('_group0', RE(r"(?=^\w+\s*\W*=)"), [RE(r"\B|\b")])]

class _group2:
    default_text_color = DELIMITER
    rules = [('_group2', _group0, [RE(r"\s*\W*=")])]

class variable:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group3:
    default_text_color = DELIMITER
    rules = [('variable', RE(r"\$\("), [RE(r"\)")], variable)]

meta_keyword = ['.PHONY']

class meta:
    default_text_color = DELIMITER
    rules = [('meta-keyword', meta_keyword)]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group1:
    default_text_color = DELIMITER
    rules = [('string', RE(r"\""), [RE(r"\"")], string), _group3.rules[0]]

rules = [
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('_group0', _group2, [RE(r"$")], _group3),
    ('section', section),
    ('meta', RE(r"^\.PHONY:"), [RE(r"$")], meta),
    ('_group1', RE(r"^\t+"), [RE(r"$")], _group1),
]
