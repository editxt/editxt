# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: xl.js
name = 'XL'
file_patterns = ['*.xl', '*.tao']

built_in = """
    in mod rem and or xor not abs sign floor ceil sqrt sin cos tan asin
    acos atan exp expm1 log log2 log10 log1p pi at text_length
    text_range text_find text_replace contains page slide basic_slide
    title_slide title subtitle fade_in fade_out fade_at clear_color
    color line_color line_width texture_wrap texture_transform texture
    scale_?x scale_?y scale_?z? translate_?x translate_?y translate_?z?
    rotate_?x rotate_?y rotate_?z? rectangle circle ellipse sphere path
    line_to move_to quad_to curve_to theme background contents locally
    time mouse_?x mouse_?y mouse_buttons ObjectLoader Animate
    MovieCredits Slides Filters Shading Materials LensFlare Mapping
    VLCAudioVideo StereoDecoder PointCloud NetworkAccess RemoteControl
    RegExp ChromaKey Snowfall NodeJS Speech Charts
    """.split()

keyword = """
    if then else do while until for loop import with is as where when by
    data constant integer real text name boolean symbol infix prefix
    postfix block tree
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

string = ('string', RE(r"\""), [RE(r"\"")])

class title0:
    default_text_color = DELIMITER
    rules = [('title', RE(r"[a-zA-Z]\w*"), [RE(r"\B|\b")])]
title0.__name__ = 'title'

class _group1:
    default_text_color = DELIMITER
    ends_with_parent = True
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'nil']),
    ]

class function:
    default_text_color = DELIMITER
    rules = [('title', title0, [RE(r"(?=->)")], _group1)]

class _group2:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'nil']),
        ('keyword', ['import']),
        string,
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false', 'nil']),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    string,
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"<<"), [RE(r">>")]),
    ('function', RE(r"(?=[a-z][^\n]*->)"), [RE(r"->")], function),
    ('_group2', RE(r"\b(?:import)"), [RE(r"$")], _group2),
    ('number', [RE(r"[0-9]+#[0-9A-Z_]+(?:\.[0-9-A-Z_]+)?#?(?:[Ee][+-]?[0-9]+)?")]),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
]