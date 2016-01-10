# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: gams.js
name = 'GAMS'
file_patterns = ['*.gams', '*.gms']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    abort acronym acronyms alias all and assign binary card diag display
    else1 eps eq equation equations file files for1 free ge gt if inf
    integer le loop lt maximizing minimizing model models na ne negative
    no not option options or ord parameter parameters positive prod
    putpage puttl repeat sameas scalar scalars semicont semiint set1
    sets smax smin solve sos1 sos2 sum system table then until using
    variable variables while1 xor yes
    """.split()

number = ('number', [RE(r"\b\d+(?:\.\d+)?")])

class _group1:
    default_text_color = DELIMITER
    rules = [number]

class _group0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['sets', 'parameters', 'variables', 'equations']),
        ('_group1', RE(r"/"), [RE(r"/")], _group1),
    ]

rules = [
    ('keyword', keyword),
    ('_group0', RE(r"\b(?:sets|parameters|variables|equations)"), [RE(r";")], _group0),
    ('string', RE(r"\*{3}"), [RE(r"\*{3}")]),
    number,
    ('number', [RE(r"\$[a-zA-Z0-9]+")]),
]
