# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: rib.js
name = 'RenderMan RIB'
file_patterns = ['*.rib']

keyword = """
    ArchiveRecord AreaLightSource Atmosphere Attribute AttributeBegin
    AttributeEnd Basis Begin Blobby Bound Clipping ClippingPlane Color
    ColorSamples ConcatTransform Cone CoordinateSystem CoordSysTransform
    CropWindow Curves Cylinder DepthOfField Detail DetailRange Disk
    Displacement Display End ErrorHandler Exposure Exterior Format
    FrameAspectRatio FrameBegin FrameEnd GeneralPolygon
    GeometricApproximation Geometry Hider Hyperboloid Identity
    Illuminate Imager Interior LightSource MakeCubeFaceEnvironment
    MakeLatLongEnvironment MakeShadow MakeTexture Matte MotionBegin
    MotionEnd NuPatch ObjectBegin ObjectEnd ObjectInstance Opacity
    Option Orientation Paraboloid Patch PatchMesh Perspective
    PixelFilter PixelSamples PixelVariance Points PointsGeneralPolygons
    PointsPolygons Polygon Procedural Projection Quantize ReadArchive
    RelativeDetail ReverseOrientation Rotate Scale ScreenWindow
    ShadingInterpolation ShadingRate Shutter Sides Skew SolidBegin
    SolidEnd Sphere SubdivisionMesh Surface TextureCoordinates Torus
    Transform TransformBegin TransformEnd TransformPoints Translate
    TrimCurve WorldBegin WorldEnd
    """.split()

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('number', number),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
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
