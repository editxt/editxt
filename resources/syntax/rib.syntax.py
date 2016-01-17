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

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('number', number),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
]