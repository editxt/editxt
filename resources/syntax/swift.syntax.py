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

number = [
    RE(r"\b(?:[\d_]+(?:\.[\deE_]+)?|0x[a-fA-F0-9_]+(?:\.[a-fA-F0-9p_]+)?|0b[01_]+|0o[0-7_]+)\b"),
]

number0 = ('number', number)

class subst:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'nil']),
        number0,
    ]

class string:
    default_text_color = DELIMITER
    rules = [
        ('subst', RE(r"\\\("), [RE(r"\)")], subst),
        ('operator.escape', [RE(r"\\[\s\S]")]),
    ]

string0 = ('string', RE(r"\""), [RE(r"\"")], string)

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"//"), [RE(r"$")], comment)

comment1 = ('comment', RE(r"/\*"), [RE(r"\*/")], comment)

class _function0:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r"{")])]
_function0.__name__ = '_function'

class params:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'nil']),
        number0,
        string0,
        comment1,
        # ignore {'begin': ':'},
    ]

class params1:
    default_text_color = DELIMITER
    rules = [('params', RE(r"\("), [RE(r"\)")], params)]
params1.__name__ = 'params'

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['func']),
        ('title', [RE(r"[A-Za-z$_][0-9A-Za-z$_]*")]),
        ('_group1', RE(r"<"), [RE(r">")]),
    ]

class _class0:
    default_text_color = DELIMITER
    rules = [('_class', [RE(r"\{")])]
_class0.__name__ = '_class'

class class0:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'nil']),
        ('keyword', ['struct', 'protocol', 'class', 'extension', 'enum']),
        ('title', [RE(r"[A-Za-z$_][0-9A-Za-z$_]*")]),
    ]
class0.__name__ = 'class'

meta = [
    RE(r"(?:@warn_unused_result|@exported|@lazy|@noescape|@NSCopying|@NSManaged|@objc|@convention|@required|@noreturn|@IBAction|@IBDesignable|@IBInspectable|@IBOutlet|@infix|@prefix|@postfix|@autoclosure|@testable|@available|@nonobjc|@NSApplicationMain|@UIApplicationMain)"),
]

class _group3:
    default_text_color = DELIMITER
    rules = [('keyword', ['import']), comment0, comment1]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false', 'nil']),
    string0,
    comment0,
    comment1,
    ('type', [RE(r"\b[A-Z][\w']*")]),
    number0,
    ('function', RE(r"\b(?:func)"), [_function0, params1], function),
    ('class', RE(r"\b(?:struct|protocol|class|extension|enum)"), [_class0], class0),
    ('meta', meta),
    ('_group3', RE(r"\b(?:import)"), [RE(r"$")], _group3),
]