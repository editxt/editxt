# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: ruleslanguage.js
name = 'Oracle Rules Language'
file_patterns = ['*.ruleslanguage']

built_in = """
    IDENTIFIER OPTIONS XML_ELEMENT XML_OP XML_ELEMENT_OF DOMDOCCREATE
    DOMDOCLOADFILE DOMDOCLOADXML DOMDOCSAVEFILE DOMDOCGETROOT
    DOMDOCADDPI DOMNODEGETNAME DOMNODEGETTYPE DOMNODEGETVALUE
    DOMNODEGETCHILDCT DOMNODEGETFIRSTCHILD DOMNODEGETSIBLING
    DOMNODECREATECHILDELEMENT DOMNODESETATTRIBUTE
    DOMNODEGETCHILDELEMENTCT DOMNODEGETFIRSTCHILDELEMENT
    DOMNODEGETSIBLINGELEMENT DOMNODEGETATTRIBUTECT DOMNODEGETATTRIBUTEI
    DOMNODEGETATTRIBUTEBYNAME DOMNODEGETBYNAME
    """.split()

keyword = """
    BILL_PERIOD BILL_START BILL_STOP RS_EFFECTIVE_START
    RS_EFFECTIVE_STOP RS_JURIS_CODE RS_OPCO_CODE INTDADDATTRIBUTE
    INTDADDVMSG INTDBLOCKOP INTDBLOCKOPNA INTDCLOSE INTDCOUNT
    INTDCOUNTSTATUSCODE INTDCREATEMASK INTDCREATEDAYMASK
    INTDCREATEFACTORMASK INTDCREATEHANDLE INTDCREATEOVERRIDEDAYMASK
    INTDCREATEOVERRIDEMASK INTDCREATESTATUSCODEMASK INTDCREATETOUPERIOD
    INTDDELETE INTDDIPTEST INTDEXPORT INTDGETERRORCODE
    INTDGETERRORMESSAGE INTDISEQUAL INTDJOIN INTDLOAD INTDLOADACTUALCUT
    INTDLOADDATES INTDLOADHIST INTDLOADLIST INTDLOADLISTDATES
    INTDLOADLISTENERGY INTDLOADLISTHIST INTDLOADRELATEDCHANNEL
    INTDLOADSP INTDLOADSTAGING INTDLOADUOM INTDLOADUOMDATES
    INTDLOADUOMHIST INTDLOADVERSION INTDOPEN INTDREADFIRST INTDREADNEXT
    INTDRECCOUNT INTDRELEASE INTDREPLACE INTDROLLAVG INTDROLLPEAK
    INTDSCALAROP INTDSCALE INTDSETATTRIBUTE INTDSETDSTPARTICIPANT
    INTDSETSTRING INTDSETVALUE INTDSETVALUESTATUS INTDSHIFTSTARTTIME
    INTDSMOOTH INTDSORT INTDSPIKETEST INTDSUBSET INTDTOU INTDTOURELEASE
    INTDTOUVALUE INTDUPDATESTATS INTDVALUE STDEV INTDDELETEEX
    INTDLOADEXACTUAL INTDLOADEXCUT INTDLOADEXDATES INTDLOADEX
    INTDLOADEXRELATEDCHANNEL INTDSAVEEX MVLOAD MVLOADACCT
    MVLOADACCTDATES MVLOADACCTHIST MVLOADDATES MVLOADHIST MVLOADLIST
    MVLOADLISTDATES MVLOADLISTHIST IF FOR NEXT DONE SELECT END CALL
    ABORT CLEAR CHANNEL FACTOR LIST NUMBER OVERRIDE SET WEEK
    DISTRIBUTIONNODE ELSE WHEN THEN OTHERWISE IENUM CSV INCLUDE LEAVE
    RIDER SAVE DELETE NOVALUE SECTION WARN SAVE_UPDATE DETERMINANT LABEL
    REPORT REVENUE EACH IN FROM TOTAL CHARGE BLOCK AND OR CSV_FILE
    RATE_CODE AUXILIARY_DEMAND UIDACCOUNT RS BILL_PERIOD_SELECT
    HOURS_PER_MONTH INTD_ERROR_STOP SEASON_SCHEDULE_NAME ACCOUNTFACTOR
    ARRAYUPPERBOUND CALLSTOREDPROC GETADOCONNECTION GETCONNECT
    GETDATASOURCE GETQUALIFIER GETUSERID HASVALUE LISTCOUNT LISTOP
    LISTUPDATE LISTVALUE PRORATEFACTOR RSPRORATE SETBINPATH SETDBMONITOR
    WQ_OPEN BILLINGHOURS DATE DATEFROMFLOAT DATETIMEFROMSTRING
    DATETIMETOSTRING DATETOFLOAT DAY DAYDIFF DAYNAME DBDATETIME HOUR
    MINUTE MONTH MONTHDIFF MONTHHOURS MONTHNAME ROUNDDATE
    SAMEWEEKDAYLASTYEAR SECOND WEEKDAY WEEKDIFF YEAR YEARDAY YEARSTR
    COMPSUM HISTCOUNT HISTMAX HISTMIN HISTMINNZ HISTVALUE MAXNRANGE
    MAXRANGE MINRANGE COMPIKVA COMPKVA COMPKVARFROMKQKW COMPLF IDATTR
    FLAG LF2KW LF2KWH MAXKW POWERFACTOR READING2USAGE AVGSEASON
    MAXSEASON MONTHLYMERGE SEASONVALUE SUMSEASON ACCTREADDATES
    ACCTTABLELOAD CONFIGADD CONFIGGET CREATEOBJECT CREATEREPORT
    EMAILCLIENT EXPBLKMDMUSAGE EXPMDMUSAGE EXPORT_USAGE FACTORINEFFECT
    GETUSERSPECIFIEDSTOP INEFFECT ISHOLIDAY RUNRATE SAVE_PROFILE
    SETREPORTTITLE USEREXIT WATFORRUNRATE TO TABLE ACOS ASIN ATAN ATAN2
    BITAND CEIL COS COSECANT COSH COTANGENT DIVQUOT DIVREM EXP FABS
    FLOOR FMOD FREPM FREXPN LOG LOG10 MAX MAXN MIN MINNZ MODF POW ROUND
    ROUND2VALUE ROUNDINT SECANT SIN SINH SQROOT TAN TANH FLOAT2STRING
    FLOAT2STRINGNC INSTR LEFT LEN LTRIM MID RIGHT RTRIM STRING STRINGNC
    TOLOWER TOUPPER TRIM NUMDAYS READ_DATE STAGING
    """.split()

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

literal = [RE(r"#\s+[a-zA-Z\ \.]*")]

literal0 = [RE(r"#[a-zA-Z\ \.]+")]

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

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('literal', literal),
    ('literal', literal0),
]
