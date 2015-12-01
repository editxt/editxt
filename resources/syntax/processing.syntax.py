# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: processing.js
name = 'Processing'
file_patterns = ['*.processing']

built_in = [
    'displayHeight',
    'displayWidth',
    'mouseY',
    'mouseX',
    'mousePressed',
    'pmouseX',
    'pmouseY',
    'key',
    'keyCode',
    'pixels',
    'focused',
    'frameCount',
    'frameRate',
    'height',
    'width',
    'size',
    'createGraphics',
    'beginDraw',
    'createShape',
    'loadShape',
    'PShape',
    'arc',
    'ellipse',
    'line',
    'point',
    'quad',
    'rect',
    'triangle',
    'bezier',
    'bezierDetail',
    'bezierPoint',
    'bezierTangent',
    'curve',
    'curveDetail',
    'curvePoint',
    'curveTangent',
    'curveTightness',
    'shape',
    'shapeMode',
    'beginContour',
    'beginShape',
    'bezierVertex',
    'curveVertex',
    'endContour',
    'endShape',
    'quadraticVertex',
    'vertex',
    'ellipseMode',
    'noSmooth',
    'rectMode',
    'smooth',
    'strokeCap',
    'strokeJoin',
    'strokeWeight',
    'mouseClicked',
    'mouseDragged',
    'mouseMoved',
    'mousePressed',
    'mouseReleased',
    'mouseWheel',
    'keyPressed',
    'keyPressedkeyReleased',
    'keyTyped',
    'print',
    'println',
    'save',
    'saveFrame',
    'day',
    'hour',
    'millis',
    'minute',
    'month',
    'second',
    'year',
    'background',
    'clear',
    'colorMode',
    'fill',
    'noFill',
    'noStroke',
    'stroke',
    'alpha',
    'blue',
    'brightness',
    'color',
    'green',
    'hue',
    'lerpColor',
    'red',
    'saturation',
    'modelX',
    'modelY',
    'modelZ',
    'screenX',
    'screenY',
    'screenZ',
    'ambient',
    'emissive',
    'shininess',
    'specular',
    'add',
    'createImage',
    'beginCamera',
    'camera',
    'endCamera',
    'frustum',
    'ortho',
    'perspective',
    'printCamera',
    'printProjection',
    'cursor',
    'frameRate',
    'noCursor',
    'exit',
    'loop',
    'noLoop',
    'popStyle',
    'pushStyle',
    'redraw',
    'binary',
    'boolean',
    'byte',
    'char',
    'float',
    'hex',
    'int',
    'str',
    'unbinary',
    'unhex',
    'join',
    'match',
    'matchAll',
    'nf',
    'nfc',
    'nfp',
    'nfs',
    'split',
    'splitTokens',
    'trim',
    'append',
    'arrayCopy',
    'concat',
    'expand',
    'reverse',
    'shorten',
    'sort',
    'splice',
    'subset',
    'box',
    'sphere',
    'sphereDetail',
    'createInput',
    'createReader',
    'loadBytes',
    'loadJSONArray',
    'loadJSONObject',
    'loadStrings',
    'loadTable',
    'loadXML',
    'open',
    'parseXML',
    'saveTable',
    'selectFolder',
    'selectInput',
    'beginRaw',
    'beginRecord',
    'createOutput',
    'createWriter',
    'endRaw',
    'endRecord',
    'PrintWritersaveBytes',
    'saveJSONArray',
    'saveJSONObject',
    'saveStream',
    'saveStrings',
    'saveXML',
    'selectOutput',
    'popMatrix',
    'printMatrix',
    'pushMatrix',
    'resetMatrix',
    'rotate',
    'rotateX',
    'rotateY',
    'rotateZ',
    'scale',
    'shearX',
    'shearY',
    'translate',
    'ambientLight',
    'directionalLight',
    'lightFalloff',
    'lights',
    'lightSpecular',
    'noLights',
    'normal',
    'pointLight',
    'spotLight',
    'image',
    'imageMode',
    'loadImage',
    'noTint',
    'requestImage',
    'tint',
    'texture',
    'textureMode',
    'textureWrap',
    'blend',
    'copy',
    'filter',
    'get',
    'loadPixels',
    'set',
    'updatePixels',
    'blendMode',
    'loadShader',
    'PShaderresetShader',
    'shader',
    'createFont',
    'loadFont',
    'text',
    'textFont',
    'textAlign',
    'textLeading',
    'textMode',
    'textSize',
    'textWidth',
    'textAscent',
    'textDescent',
    'abs',
    'ceil',
    'constrain',
    'dist',
    'exp',
    'floor',
    'lerp',
    'log',
    'mag',
    'map',
    'max',
    'min',
    'norm',
    'pow',
    'round',
    'sq',
    'sqrt',
    'acos',
    'asin',
    'atan',
    'atan2',
    'cos',
    'degrees',
    'radians',
    'sin',
    'tan',
    'noise',
    'noiseDetail',
    'noiseSeed',
    'random',
    'randomGaussian',
    'randomSeed',
]

keyword = [
    'BufferedReader',
    'PVector',
    'PFont',
    'PImage',
    'PGraphics',
    'HashMap',
    'boolean',
    'byte',
    'char',
    'color',
    'double',
    'float',
    'int',
    'long',
    'String',
    'Array',
    'FloatDict',
    'FloatList',
    'IntDict',
    'IntList',
    'JSONArray',
    'JSONObject',
    'Object',
    'StringDict',
    'StringList',
    'Table',
    'TableRow',
    'XML',
    'false',
    'synchronized',
    'int',
    'abstract',
    'float',
    'private',
    'char',
    'boolean',
    'static',
    'null',
    'if',
    'const',
    'for',
    'true',
    'while',
    'long',
    'throw',
    'strictfp',
    'finally',
    'protected',
    'import',
    'native',
    'final',
    'return',
    'void',
    'enum',
    'else',
    'break',
    'transient',
    'new',
    'catch',
    'instanceof',
    'byte',
    'super',
    'volatile',
    'case',
    'assert',
    'short',
    'package',
    'default',
    'double',
    'public',
    'try',
    'this',
    'switch',
    'continue',
    'throws',
    'protected',
    'public',
    'private',
]

literal = ['P2D', 'P3D', 'HALF_PI', 'PI', 'QUARTER_PI', 'TAU', 'TWO_PI']

title = ['setup', 'draw']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'type': 'RegExp', 'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b"}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

class string:
    default_text = DELIMITER
    rules = [
        # {'relevance': 0, 'begin': '\\\\[\\s\\S]'},
    ]

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('title', title),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
]

# TODO merge "word_groups" and "delimited_ranges" into "rules" in editxt.syntax
assert "__obj" not in globals()
assert "__fixup" not in globals()
def __fixup(obj):
    groups = []
    ranges = []
    rules = getattr(obj, "rules", [])
    for i, rng in reversed(list(enumerate(rules))):
        if len(rng) == 2:
            groups.append(rng)
        else:
            assert len(rng) > 2, rng
            ranges.append(rng)
    return groups, ranges

class __obj:
    rules = globals().get("rules", [])
word_groups, delimited_ranges = __fixup(__obj)

for __obj in globals().values():
    if hasattr(__obj, "rules"):
        __obj.word_groups, __obj.delimited_ranges = __fixup(__obj)

del __obj, __fixup
