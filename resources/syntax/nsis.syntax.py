# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: nsis.js
name = 'NSIS'
file_patterns = ['*.nsis']

keyword = """
    Abort AddBrandingImage AddSize AllowRootDirInstall AllowSkipFiles
    AutoCloseWindow BGFont BGGradient BrandingText BringToFront Call
    CallInstDLL Caption ChangeUI CheckBitmap ClearErrors CompletedText
    ComponentText CopyFiles CRCCheck CreateDirectory CreateFont
    CreateShortCut Delete DeleteINISec DeleteINIStr DeleteRegKey
    DeleteRegValue DetailPrint DetailsButtonText DirText DirVar
    DirVerify EnableWindow EnumRegKey EnumRegValue Exch Exec ExecShell
    ExecWait ExpandEnvStrings File FileBufSize FileClose FileErrorText
    FileOpen FileRead FileReadByte FileReadUTF16LE FileReadWord FileSeek
    FileWrite FileWriteByte FileWriteUTF16LE FileWriteWord FindClose
    FindFirst FindNext FindWindow FlushINI FunctionEnd GetCurInstType
    GetCurrentAddress GetDlgItem GetDLLVersion GetDLLVersionLocal
    GetErrorLevel GetFileTime GetFileTimeLocal GetFullPathName
    GetFunctionAddress GetInstDirError GetLabelAddress GetTempFileName
    Goto HideWindow Icon IfAbort IfErrors IfFileExists IfRebootFlag
    IfSilent InitPluginsDir InstallButtonText InstallColors InstallDir
    InstallDirRegKey InstProgressFlags InstType InstTypeGetText
    InstTypeSetText IntCmp IntCmpU IntFmt IntOp IsWindow LangString
    LicenseBkColor LicenseData LicenseForceSelection LicenseLangString
    LicenseText LoadLanguageFile LockWindow LogSet LogText
    ManifestDPIAware ManifestSupportedOS MessageBox MiscButtonText Name
    Nop OutFile Page PageCallbacks PageExEnd Pop Push Quit ReadEnvStr
    ReadINIStr ReadRegDWORD ReadRegStr Reboot RegDLL Rename
    RequestExecutionLevel ReserveFile Return RMDir SearchPath SectionEnd
    SectionGetFlags SectionGetInstTypes SectionGetSize SectionGetText
    SectionGroupEnd SectionIn SectionSetFlags SectionSetInstTypes
    SectionSetSize SectionSetText SendMessage SetAutoClose
    SetBrandingImage SetCompress SetCompressor SetCompressorDictSize
    SetCtlColors SetCurInstType SetDatablockOptimize SetDateSave
    SetDetailsPrint SetDetailsView SetErrorLevel SetErrors
    SetFileAttributes SetFont SetOutPath SetOverwrite SetPluginUnload
    SetRebootFlag SetRegView SetShellVarContext SetSilent
    ShowInstDetails ShowUninstDetails ShowWindow SilentInstall
    SilentUnInstall Sleep SpaceTexts StrCmp StrCmpS StrCpy StrLen
    SubCaption SubSectionEnd Unicode UninstallButtonText
    UninstallCaption UninstallIcon UninstallSubCaption UninstallText
    UninstPage UnRegDLL Var VIAddVersionKey VIFileVersion
    VIProductVersion WindowIcon WriteINIStr WriteRegBin WriteRegDWORD
    WriteRegExpandStr WriteRegStr WriteUninstaller XPStyle
    """.split()

literal = """
    admin all auto both colored current false force hide highest
    lastused leave listonly none normal notset off on open print show
    silent silentlog smooth textonly true user
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

variable = [
    RE(r"\$(?:ADMINTOOLS|APPDATA|CDBURN_AREA|CMDLINE|COMMONFILES32|COMMONFILES64|COMMONFILES|COOKIES|DESKTOP|DOCUMENTS|EXEDIR|EXEFILE|EXEPATH|FAVORITES|FONTS|HISTORY|HWNDPARENT|INSTDIR|INTERNET_CACHE|LANGUAGE|LOCALAPPDATA|MUSIC|NETHOOD|OUTDIR|PICTURES|PLUGINSDIR|PRINTHOOD|PROFILE|PROGRAMFILES32|PROGRAMFILES64|PROGRAMFILES|QUICKLAUNCH|RECENT|RESOURCES_LOCALIZED|RESOURCES|SENDTO|SMPROGRAMS|SMSTARTUP|STARTMENU|SYSDIR|TEMP|TEMPLATES|VIDEOS|WINDIR)"),
]

variable1 = ('variable', [RE(r"\$+{[a-zA-Z0-9_]+}")])

variable2 = ('variable', [RE(r"\$+[a-zA-Z0-9_]+")])

variable3 = ('variable', [RE(r"\$+\([a-zA-Z0-9_]+\)")])

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\$(\\\\(n|r|t)|\\$)'},
        ('variable', variable),
        variable1,
        variable2,
        variable3,
    ]

keyword1 = [
    RE(r"\!(?:addincludedir|addplugindir|appendfile|cd|define|delfile|echo|else|endif|error|execute|finalize|getdllversionsystem|ifdef|ifmacrodef|ifmacrondef|ifndef|if|include|insertmacro|macroend|macro|makensis|packhdr|searchparse|searchreplace|tempfile|undef|verbose|warning)"),
]

built_in = [
    RE(r"(?:ARCHIVE|FILE_ATTRIBUTE_ARCHIVE|FILE_ATTRIBUTE_NORMAL|FILE_ATTRIBUTE_OFFLINE|FILE_ATTRIBUTE_READONLY|FILE_ATTRIBUTE_SYSTEM|FILE_ATTRIBUTE_TEMPORARY|HKCR|HKCU|HKDD|HKEY_CLASSES_ROOT|HKEY_CURRENT_CONFIG|HKEY_CURRENT_USER|HKEY_DYN_DATA|HKEY_LOCAL_MACHINE|HKEY_PERFORMANCE_DATA|HKEY_USERS|HKLM|HKPD|HKU|IDABORT|IDCANCEL|IDIGNORE|IDNO|IDOK|IDRETRY|IDYES|MB_ABORTRETRYIGNORE|MB_DEFBUTTON1|MB_DEFBUTTON2|MB_DEFBUTTON3|MB_DEFBUTTON4|MB_ICONEXCLAMATION|MB_ICONINFORMATION|MB_ICONQUESTION|MB_ICONSTOP|MB_OK|MB_OKCANCEL|MB_RETRYCANCEL|MB_RIGHT|MB_RTLREADING|MB_SETFOREGROUND|MB_TOPMOST|MB_USERICON|MB_YESNO|NORMAL|OFFLINE|READONLY|SHCTX|SHELL_CONTEXT|SYSTEM|TEMPORARY)"),
]

rules = [
    ('keyword', keyword),
    ('literal', literal),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('comment', RE(r";"), [RE(r"$")], comment),
    ('function', RE(r"\b(?:Function|PageEx|Section|SectionGroup|SubSection)"), [RE(r"$")]),
    ('keyword', keyword1),
    variable1,
    variable2,
    variable3,
    ('built_in', built_in),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
    # ignore {'begin': '[a-zA-Z]\\w*::[a-zA-Z]\\w*'},
]