# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: gradle.js
name = 'Gradle'
file_patterns = ['*.gradle']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    task project allprojects subprojects artifacts buildscript
    configurations dependencies repositories sourceSets description
    delete from into include exclude source classpath destinationDir
    includes options sourceCompatibility targetCompatibility group
    flatDir doLast doFirst flatten todir fromdir ant def abstract break
    case catch continue default do else extends final finally for if
    implements instanceof native new private protected public return
    static switch synchronized throw throws transient try volatile while
    strictfp package import false null super this true antlrtask
    checkstyle codenarc copy boolean byte char class double float int
    interface long short void compile runTime file fileTree abs any
    append asList asWritable call collect compareTo count div dump each
    eachByte eachFile eachLine every find findAll flatten getAt getErr
    getIn getOut getText grep immutable inject inspect intersect
    invokeMethods isCase join leftShift minus multiply newInputStream
    newOutputStream newPrintWriter newReader newWriter next plus pop
    power previous print println push putAt read readBytes readLines
    reverse reverseEach round size sort splitEachLine step subMap times
    toInteger toList tokenize upto waitForOrKill withPrintWriter
    withReader withStream withWriter withWriterAppend write writeLine
    """.split()

number = [RE(r"\b\d+(?:\.\d+)?")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group0:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class regexp:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        ('_group0', RE(r"\["), [RE(r"\]")], _group0),
    ]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('regexp', RE(r"\/"), [RE(r"\/[gimuy]*")], regexp),
]
