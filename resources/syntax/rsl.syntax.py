# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: rsl.js
name = 'RenderMan RSL'
file_patterns = ['*.rsl']

built_in = """
    abs acos ambient area asin atan atmosphere attribute calculatenormal
    ceil cellnoise clamp comp concat cos degrees depth Deriv diffuse
    distance Du Dv environment exp faceforward filterstep floor format
    fresnel incident length lightsource log match max min mod noise
    normalize ntransform opposite option phong pnoise pow printf ptlined
    radians random reflect refract renderinfo round setcomp setxcomp
    setycomp setzcomp shadow sign sin smoothstep specular specularbrdf
    spline sqrt step tan texture textureinfo trace transform vtransform
    xcomp ycomp zcomp
    """.split()

keyword = """
    float color point normal vector matrix while for if do return else
    break extern continue
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

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('number', number),
    ('meta', RE(r"#"), [RE(r"$")]),
    ('class', RE(r"\b(?:surface|displacement|light|volume|imager)"), [RE(r"\(")]),
    ('_group1', RE(r"\b(?:illuminate|illuminance|gather)"), [RE(r"\(")]),
]