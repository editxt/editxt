# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: swift.js
name = 'Swift'
file_patterns = ['*.swift']

built_in = """
    abs advance alignof alignofValue anyGenerator assert
    assertionFailure bridgeFromObjectiveC
    bridgeFromObjectiveCUnconditional bridgeToObjectiveC
    bridgeToObjectiveCUnconditional c contains count countElements
    countLeadingZeros debugPrint debugPrintln distance dropFirst
    dropLast dump encodeBitsAsWords enumerate equal fatalError filter
    find getBridgedObjectiveCType getVaList indices insertionSort
    isBridgedToObjectiveC isBridgedVerbatimToObjectiveC
    isUniquelyReferenced isUniquelyReferencedNonObjC join lazy
    lexicographicalCompare map max maxElement min minElement numericCast
    overlaps partition posix precondition preconditionFailure print
    println quickSort readLine reduce reflect reinterpretCast reverse
    roundUpToAlignment sizeof sizeofValue sort split startsWith stride
    strideof strideofValue swap toString transcode underestimateCount
    unsafeAddressOf unsafeBitCast unsafeDowncast unsafeUnwrap
    unsafeReflect withExtendedLifetime withObjectAtPlusZero
    withUnsafePointer withUnsafePointerToObject withUnsafeMutablePointer
    withUnsafeMutablePointers withUnsafePointer withUnsafePointers
    withVaList zip
    """.split()

keyword = """
    __COLUMN__ __FILE__ __FUNCTION__ __LINE__ as as! as? associativity
    break case catch class continue convenience default defer deinit
    didSet do dynamic dynamicType else enum extension fallthrough false
    final for func get guard if import in indirect infix init inout
    internal is lazy left let mutating nil none nonmutating operator
    optional override postfix precedence prefix private protocol
    Protocol public repeat required rethrows return right self Self set
    static struct subscript super switch throw throws true try try! try?
    Type typealias unowned var weak where while willSet
    """.split()

literal = ['true', 'false', 'nil']

number = [
    RE(r"\b(?:[\d_]+(?:\.[\deE_]+)?|0x[a-fA-F0-9_]+(?:\.[a-fA-F0-9p_]+)?|0b[01_]+|0o[0-7_]+)\b"),
]

class subst:
    default_text = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', literal),
        ('number', number),
    ]

class string:
    default_text = DELIMITER
    rules = [
        ('subst', RE(r"\\\("), [RE(r"\)")], subst),
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

type = [RE(r"\b[A-Z][\w']*")]

class _function:
    default_text = DELIMITER
    rules = [('_function', RE(r"{"), [RE(r'\b|\B')])]

keyword0 = ['func']

title = [RE(r"[A-Za-z$_][0-9A-Za-z$_]*")]

class params:
    default_text = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', literal),
        ('number', number),
        None,  # rules[3],
        ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
        # {'begin': ':'},
    ]

class params0:
    default_text = DELIMITER
    rules = [('params', RE(r"\("), [RE(r"\)")], params)]
params0.__name__ = 'params'

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('title', title),
        ('_group1', RE(r"<"), [RE(r">")]),
    ]

class _class:
    default_text = DELIMITER
    rules = [('_class', RE(r"\{"), [RE(r'\b|\B')])]

class class0:
    default_text = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', literal),
        ('title', title),
    ]
class0.__name__ = 'class'

meta = [
    RE(r"(?:@warn_unused_result|@exported|@lazy|@noescape|@NSCopying|@NSManaged|@objc|@convention|@required|@noreturn|@IBAction|@IBDesignable|@IBInspectable|@IBOutlet|@infix|@prefix|@postfix|@autoclosure|@testable|@available|@nonobjc|@NSApplicationMain|@UIApplicationMain)"),
]

keyword1 = ['import']

class _group3:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword1),
        None,  # rules[4],
        None,  # rules[5],
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('type', type),
    ('number', number),
    ('function', RE(r"\b(?:func)"), [_function, params0], function),
    ('class', RE(r"\b(?:struct|protocol|class|extension|enum)"), [_class], class0),
    ('meta', meta),
    ('_group3', RE(r"\b(?:import)"), [RE(r"$")], _group3),
]

params.rules[4] = rules[3]
_group3.rules[1] = rules[4]
_group3.rules[2] = rules[5]

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
