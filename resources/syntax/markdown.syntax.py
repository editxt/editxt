# -*- coding: UTF-8 -*-
# Adapted from highlight.js markdown syntax definition
# source: markdown.js
name = 'Markdown'
file_patterns = ['*.markdown', '*.md', '*.mkdown', '*.mkd']

section = [RE(r"^.+?\n[=-]{2,}$")]

bullet = [RE(r"^(?:[*+-]|(?:\d+\.))\s+")]

strong = [RE(r"[*_]{2}.+?[*_]{2}")]

emphasis = [RE(r"\*.+?\*")]

emphasis0 = [RE(r"_.+?_")]

code = [RE(r"``[^`\n]+``"), RE(r"`[^`\n]+`")]

class _string:
    default_text_color = DELIMITER
    rules = [('_string', [RE(r"\[")])]

class _link:
    default_text_color = DELIMITER
    rules = [('_link', [RE(r"\]\(")])]

class _link0:
    default_text_color = DELIMITER
    rules = [('_link', [RE(r"\)")])]
_link0.__name__ = '_link'

class _symbol:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\]\[")])]

class _symbol0:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\]")])]
_symbol0.__name__ = '_symbol'

class _group2:
    default_text_color = DELIMITER
    rules = [
        ('string', _string, [RE(r"(?=\])")]),
        ('link', _link, [_link0]),
        ('symbol', _symbol, [_symbol0]),
    ]

class _symbol1:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\[")])]
_symbol1.__name__ = '_symbol'

class _symbol2:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\]:")])]
_symbol2.__name__ = '_symbol'

class symbol:
    default_text_color = DELIMITER
    rules = [('symbol', _symbol1, [_symbol2])]

class _group3:
    default_text_color = DELIMITER
    rules = [('symbol', symbol, [RE(r"$")])]

rules = [
    ('section', RE(r"^#{1,6}"), [RE(r"$")]),
    ('section', section),
    ('_group0', RE(r"<"), [RE(r">")], 'xml'),
    ('bullet', bullet),
    ('strong', strong),
    ('emphasis', emphasis),
    ('emphasis', emphasis0),
    ('quote', RE(r"^>\s+"), [RE(r"$")]),
    ('code', code),
    ('code', "```", ["```"], DynamicRange(r"\S+\s*?$|", "tag")),
    ('code', RE(r"^(?: {4}|	)"), [RE(r"$")]),
    ('_group1', RE(r"^[-\*]{3,}"), [RE(r"$")]),
    ('_group2', RE(r"(?=\[.+?\][\(\[].*?[\)\]])"), [RE(r"\B\b")], _group2),
    ('_group3', RE(r"(?=^\[.+\]:)"), [RE(r"\B\b")], _group3),
]
