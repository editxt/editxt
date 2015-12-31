# EditXT syntax highlighting demo

This is based on the highlight.js demo. It was produced by using the following
find/replace pattern in EditXT plus a bit of manual editing.

Concatenate the three lines in the code block onto a single line:

```regular-expression
:[\s\S]+?<h2>(.*)</h2>[\s\S]+?<pre><code class="([^\"]+)">([\s\S]+?)\n?</code></pre>
:"## {}\n\n`\``{}\n{}\n`\``\n\n".format(match[1], match[2], __import__("html").unescape(match[3]))
: replace-all python-replace
```


## AsciiDoc

```asciidoc
Hello, World!
============
Author Name, <author@domain.foo>

you can write text http://example.com[with links], optionally
using an explicit link:http://example.com[link prefix].

* single quotes around a phrase place 'emphasis'
** alternatively, you can put underlines around a phrase to add _emphasis_
* astericks around a phrase make the text *bold*
* pluses around a phrase make it +monospaced+
* `smart' quotes using a leading backtick and trailing single quote
** use two of each for double ``smart'' quotes

- escape characters are supported
- you can escape a quote inside emphasized text like 'here\'s johnny!'

term:: definition
 another term:: another definition

// this is just a comment

Let's make a break.

'''

////
we'll be right with you

after this brief interruption.
////

== We're back!

Want to see a image::images/tiger.png[Tiger]?

.Nested highlighting
++++
<this_is inline="xml"></this_is>
++++

____
asciidoc is so powerful.
____

another quote:

[quote, Sir Arthur Conan Doyle, The Adventures of Sherlock Holmes]
____
When you have eliminated all which is impossible, then whatever remains, however improbable, must be the truth.
____

Getting Literal
---------------

 want to get literal? prefix a line with a space.

....
I'll join that party, too.
....

. one thing (yeah!)
. two thing `i can write code`, and `more` wipee!

NOTE: AsciiDoc is quite cool, you should try it.
```

## AspectJ

```aspectj
package com.aspectj.syntax;
import org.aspectj.lang.annotation.AdviceName;

privileged public aspect LoggingAspect percflowbelow(ajia.services.*){
  private pointcut getResult() : call(* *(..) throws SQLException) && args(Account, .., int);
  @AdviceName("CheckValidEmail")
  before (Customer hu) : getResult(hu){		
    System.out.println("Your mail address is valid!");
  }
  Object around() throws InsufficientBalanceException: getResult() && call(Customer.new(String,String,int,int,int)){
    return	proceed();
  }
  public Cache getCache() {
    return this.cache;
  }
  pointcut beanPropertyChange(BeanSupport bean, Object newValue): execution(void BeanSupport+.set*(*)) && args(newValue) && this(bean);
  declare parents: banking.entities.* implements BeanSupport;
  declare warning : call(void TestSoftening.perform()): "Please ensure you are not calling this from an AWT thread";
  private String Identifiable.id;
  public void Identifiable.setId(String id) {
    this.id = id;
  }
}
```

## AutoHotkey

```autohotkey
; hotkeys and hotstrings
#a::WinSet, AlwaysOnTop, Toggle, A
#Space::
  MsgBox, Percent sign (`%) need to be escaped.
  Run "C:\Program Files\some\program.exe"
  Gosub, label1
return
::btw::by the way
; volume
#Numpad8::Send {Volume_Up}
#Numpad5::Send {Volume_Mute}
#Numpad2::Send {Volume_Down}

label1:
  if (Clipboard = "")
  {
    MsgBox, , Clipboard, Empty!
  }
  else
  {
    StringReplace, temp, Clipboard, old, new, All
    MsgBox, , Clipboard, %temp%
  }
return
```

## AutoIt

```autoit
#NoTrayIcon
#AutoIt3Wrapper_Run_Tidy=Y
#include <Misc.au3>

_Singleton(@ScriptName) ; Allow only one instance
example(0, 10)

Func example($min, $max)
	For $i = $min To $max
		If Mod($i, 2) == 0 Then
			MsgBox(64, "Message", $i & ' is even number!')
		Else
			MsgBox(64, "Message", $i & ' is odd number!')
		EndIf
	Next
EndFunc   ;==>example
```

## AVR Assembler

```avrasm
;* Title:       Block Copy Routines
;* Version:     1.1

.include "8515def.inc"

        rjmp    RESET       ;reset handle

.def    flashsize=r16       ;size of block to be copied

flash2ram:
        lpm                 ;get constant
        st      Y+,r0       ;store in SRAM and increment Y-pointer
        adiw    ZL,1        ;increment Z-pointer
        dec     flashsize
        brne    flash2ram   ;if not end of table, loop more
        ret

.def    ramtemp =r1         ;temporary storage register
.def    ramsize =r16        ;size of block to be copied
```

## Axapta

```axapta
class ExchRateLoadBatch extends RunBaseBatch {
  ExchRateLoad rbc;
  container currencies;
  boolean actual;
  boolean overwrite;
  date beg;
  date end;

  #define.CurrentVersion(5)

  #localmacro.CurrentList
    currencies,
    actual,
    beg,
    end
  #endmacro
}

public boolean unpack(container packedClass) {
  container       base;
  boolean         ret;
  Integer         version    = runbase::getVersion(packedClass);

  switch (version) {
    case #CurrentVersion:
      [version, #CurrentList] = packedClass;
      return true;
    default:
      return false;
  }
  return ret;
}
```

## Bash

```bash
#!/bin/bash

###### BEGIN CONFIG
ACCEPTED_HOSTS="/root/.hag_accepted.conf"
BE_VERBOSE=false
###### END CONFIG

if [ "$UID" -ne 0 ]
then
 echo "Superuser rights is required"
 echo 'Printing the # sign'
 exit 2
fi

if test $# -eq 0
then
elif test [ $1 == 'start' ]
else
fi

genApacheConf(){
 if [[ "$2" = "www" ]]
 then
  full_domain=$1
 else
  full_domain=$2.$1
 fi
 host_root="${APACHE_HOME_DIR}$1/$2/$(title)"
 echo -e "# Host $1/$2 :"
}
```

## Brainfuck

```brainfuck
++++++++++
[ 3*10 and 10*10
  ->+++>++++++++++<<
]>>
[ filling cells
  ->++>>++>++>+>++>>++>++>++>++>++>++>++>++>++>++>++[</]<[<]<[<]>>
]<
+++++++++<<
[ rough codes correction loop
  ->>>+>+>+>+++>+>+>+>+>+>+>+>+>+>+>+>+>+>+[<]<
]
more accurate сodes correction
>>>++>
-->+++++++>------>++++++>++>+++++++++>++++++++++>++++++++>--->++++++++++>------>++++++>
++>+++++++++++>++++++++++++>------>+++
rewind and output
[<]>[.>]
```

## C/AL

```cal
OBJECT Codeunit 11 Gen. Jnl.-Check Line
{
  OBJECT-PROPERTIES
  {
    Date=09-09-14;
    Time=12:00:00;
    Version List=NAVW18.00;
  }
  PROPERTIES
  {
    TableNo=81;
    Permissions=TableData 252=rimd;
    OnRun=BEGIN
            GLSetup.GET;
            RunCheck(Rec);
          END;

  }
  CODE
  {
    VAR
      Text000@1000 : TextConst 'ENU=can only be a closing date for G/L entries';
      Text001@1001 : TextConst 'ENU=is not within your range of allowed posting dates';
      Text002@1002 : TextConst 'ENU=%1 or %2 must be G/L Account or Bank Account.';
      Text011@1011 : TextConst 'ENU=The combination of dimensions used in %1 %2, %3, %4 is blocked. %5';
      Text012@1012 : TextConst 'ENU=A dimension used in %1 %2, %3, %4 has caused an error. %5';
      GLSetup@1014 : Record 98;
      SalesDocAlreadyExistsErr@1026 : TextConst '@@@="%1 = Document Type; %2 = Document No.";ENU=Sales %1 %2 already exists.';
      PurchDocAlreadyExistsErr@1025 : TextConst '@@@="%1 = Document Type; %2 = Document No.";ENU=Purchase %1 %2 already exists.';

    PROCEDURE RunCheck@4(VAR GenJnlLine@1000 : Record 81);
    VAR
      PaymentTerms@1004 : Record 3;
      Cust@1005 : Record 18;
      Vendor@1006 : Record 23;
      ICPartner@1007 : Record 413;
      ICGLAcount@1008 : Record 410;
      TableID@1002 : ARRAY [10] OF Integer;
      No@1003 : ARRAY [10] OF Code[20];

    PROCEDURE ErrorIfPositiveAmt@2(GenJnlLine@1000 : Record 81);
    BEGIN
      IF GenJnlLine.Amount > 0 THEN
        GenJnlLine.FIELDERROR(Amount,Text008);
    END;

    PROCEDURE ErrorIfNegativeAmt@3(GenJnlLine@1000 : Record 81);
    BEGIN
      IF GenJnlLine.Amount < 0 THEN
        GenJnlLine.FIELDERROR(Amount,Text007);
    END;

    PROCEDURE SetOverDimErr@5();
    BEGIN
      OverrideDimErr := TRUE;
    END;

    PROCEDURE CheckSalesDocNoIsNotUsed@115(DocType@1000 : Option;DocNo@1001 : Code[20]);
    VAR
      OldCustLedgEntry@1002 : Record 21;
    BEGIN
      OldCustLedgEntry.SETRANGE("Document No.",DocNo);
      OldCustLedgEntry.SETRANGE("Document Type",DocType);
      IF OldCustLedgEntry.FINDFIRST THEN
        ERROR(SalesDocAlreadyExistsErr,OldCustLedgEntry."Document Type",DocNo);
    END;

    PROCEDURE CheckPurchDocNoIsNotUsed@107(DocType@1000 : Option;DocNo@1002 : Code[20]);
    VAR
      OldVendLedgEntry@1001 : Record 25;
    BEGIN
      OldVendLedgEntry.SETRANGE("Document No.",DocNo);
      OldVendLedgEntry.SETRANGE("Document Type",DocType);
      IF OldVendLedgEntry.FINDFIRST THEN
        ERROR(PurchDocAlreadyExistsErr,OldVendLedgEntry."Document Type",DocNo);
    END;

    LOCAL PROCEDURE CheckGenJnlLineDocType@7(GenJnlLine@1001 : Record 81);
  }
}
```

## Cap’n Proto

```capnproto
@0xdbb9ad1f14bf0b36;  # unique file ID, generated by `capnp id`

struct Person {
  name @0 :Text;
  birthdate @3 :Date;

  email @1 :Text;
  phones @2 :List(PhoneNumber);

  struct PhoneNumber {
    number @0 :Text;
    type @1 :Type;

    enum Type {
      mobile @0;
      home @1;
      work @2;
    }
  }
}

struct Date {
  year @0 :Int16;
  month @1 :UInt8;
  day @2 :UInt8;
  flags @3 :List(Bool) = [ true, false, false, true ];
}

interface Node {
  isDirectory @0 () -> (result :Bool);
}

interface Directory extends(Node) {
  list @0 () -> (list: List(Entry));
  struct Entry {
    name @0 :Text;
    node @1 :Node;
  }

  create @1 (name :Text) -> (file :File);
  mkdir @2 (name :Text) -> (directory :Directory)
  open @3 (name :Text) -> (node :Node);
  delete @4 (name :Text);
  link @5 (name :Text, node :Node);
}

interface File extends(Node) {
  size @0 () -> (size: UInt64);
  read @1 (startAt :UInt64 = 0, amount :UInt64 = 0xffffffffffffffff)
       -> (data: Data);
  # Default params = read entire file.

  write @2 (startAt :UInt64, data :Data);
  truncate @3 (size :UInt64);
}
```

## Ceylon

```ceylon
shared void run() {
    print("Hello, `` process.arguments.first else "World" ``!");
}
class Counter(count=0) {
    variable Integer count;
    shared Integer currentValue => count;
    shared void increment() => count++;
}
```

## Clojure REPL

```clojure-repl
user=> (defn f [x y]
  #_=>   (+ x y))
#'user/f
user=> (f 5 7)
12
user=> nil
nil
```

## Clojure

```clojure
; Comment

(def
  ^{:macro true
    :added "1.0"}
  let (fn* let [&form &env & decl] (cons 'let* decl)))

(def ^:dynamic chunk-size 17)

(defn next-chunk [rdr]
  (let [buf (char-array chunk-size)
        s (.read rdr buf)]
  (when (pos? s)
    (java.nio.CharBuffer/wrap buf 0 s))))

(defn chunk-seq [rdr]
  (when-let [chunk (next-chunk rdr)]
    (cons chunk (lazy-seq (chunk-seq rdr)))))
```

## CMake

```cmake
cmake_minimum_required(VERSION 2.8.8)
project(cmake_example)

# Show message on Linux platform
if (${CMAKE_SYSTEM_NAME} MATCHES Linux)
    message("Good choice, bro!")
endif()

# Tell CMake to run moc when necessary:
set(CMAKE_AUTOMOC ON)
# As moc files are generated in the binary dir,
# tell CMake to always look for includes there:
set(CMAKE_INCLUDE_CURRENT_DIR ON)

# Widgets finds its own dependencies.
find_package(Qt5Widgets REQUIRED)

add_executable(myproject main.cpp mainwindow.cpp)
qt5_use_modules(myproject Widgets)
```

## CoffeeScript

```coffeescript
grade = (student, period=(if b? then 7 else 6), messages={"A": "Excellent"}) ->
  if student.excellentWork
    "A+"
  else if student.okayStuff
    if student.triedHard then "B" else "B-"
  else
    "C"

square = (x) -> x * x

two = -> 2

math =
  root:   Math.sqrt
  square: square
  cube:   (x) -> x * square x

race = (winner, runners...) ->
  print winner, runners

class Animal extends Being
  constructor: (@name) ->

  move: (meters) ->
    alert @name + " moved #{meters}m."

hi = `function() {
  return [document.title, "Hello JavaScript"].join(": ");
}`

heredoc = """
CoffeeScript subst test #{ 010 + 0xf / 0b10 + "nested string #{ /\n/ }"}
"""

###
CoffeeScript Compiler v1.2.0
Released under the MIT License
###

OPERATOR = /// ^ (
?: [-=]>             # function
) ///
```

## Caché Object Script

```cos
SET test = 1
set ^global = 2
Write "Current date """, $ztimestamp, """, result: ", test + ^global = 3
do ##class(Cinema.Utils).AddShow("test") // line comment
d:(^global = 2) ..thisClassMethod(1, 2, "test")
/*
 * Multiline comment
 */
&sql(SELECT * FROM Cinema.Film WHERE Length > 2)
&js<for (var i = 0; i < String("test").split("").length); ++i) { console.log(i); }>
&html<<!DOCTYPE html><html><head><meta name="test"/></head><body>test</body></html>>
```

## C++

```cpp
#include <iostream>
#define IABS(x) ((x) < 0 ? -(x) : (x))

int main(int argc, char *argv[]) {

  /* An annoying "Hello World" example */
  for (auto i = 0; i < 0xFFFF; i++)
    cout << "Hello, World!" << endl;

  char c = '\n';
  unordered_map <string, vector<string> > m;
  m["key"] = "\\\\"; // this is an error

  return -2e3 + 12l;
}
```

## crmsh

```crmsh
node webui
node 168633611: node1
rsc_template web-server apache \
	params port=8000 \
	op monitor interval=10s
# Never use this STONITH agent in production!
primitive development-stonith stonith:null \
	params hostlist="webui node1 node2 node3"
primitive proxy systemd:haproxy \
	op monitor interval=10s
primitive proxy-vip IPaddr2 \
	params ip=10.13.37.20
primitive srv1 @web-server
primitive srv2 @web-server
primitive test1 Dummy
primitive test2 IPaddr2 \
	params ip=10.13.37.99
primitive vip1 IPaddr2 \
	params ip=10.13.37.21 \
	op monitor interval=20s
primitive vip2 IPaddr2 \
	params ip=10.13.37.22 \
	op monitor interval=20s
group g-proxy proxy-vip proxy
group g-serv1 vip1 srv1
group g-serv2 vip2 srv2
# Never put the two web servers on the same node
colocation co-serv -inf: g-serv1 g-serv2
# Never put any web server or haproxy on webui
location l-avoid-webui { g-proxy g-serv1 g-serv2 } -inf: webui
# Prever to spread groups across nodes
location l-proxy g-proxy 200: node1
location l-serv1 g-serv1 200: node2
location l-serv2 g-serv2 200: node3
property cib-bootstrap-options: \
	stonith-enabled=true \
	no-quorum-policy=ignore \
	placement-strategy=balanced \
	have-watchdog=false \
	dc-version="1.1.13-1.1.13+git20150827.e8888b9" \
	cluster-infrastructure=corosync \
	cluster-name=hacluster
rsc_defaults rsc-options: \
	resource-stickiness=1 \
	migration-threshold=3
op_defaults op-options: \
	timeout=600 \
	record-pending=true
```

## Crystal

```crystal
class Person
  def initialize(@name)
  end

  def greet
    puts "Hi, I'm #{@name}"
  end
end

class Employee < Person
end

employee = Employee.new "John"
employee.greet #=> "Hi, I'm John"
employee.is_a?(Person) #=> true

@[Link("m")]
lib C
  # In C: double cos(double x)
  fun cos(value : Float64) : Float64
end

C.cos(1.5_f64) #=> 0.0707372
```

## C#

```cs
using System;

#pragma warning disable 414, 3021

public class Program
{
    /// <summary>The entry point to the program.</summary>
    public static int Main(string[] args)
    {
        Console.WriteLine("Hello, World!");
        string s = @"This
""string""
spans
multiple
lines!";

        dynamic x = new ExpandoObject();
        x.MyProperty = 2;

        return 0;
    }
}

async Task<int> AccessTheWebAsync()
{
    // ...
    string urlContents = await getStringTask;
    return urlContents.Length;
}

internal static void ExceptionFilters()
{
  try 
  {
      throw new Exception();
  }
  catch (Exception e) when (e.Message == "My error") { }
}
```

## CSS

```css
@media screen and (-webkit-min-device-pixel-ratio: 0) {
  body:first-of-type pre::after {
    content: 'highlight: ' attr(class);
  }
  body {
    background: linear-gradient(45deg, blue, red);
  }
}

@import url('print.css');
@page:right {
 margin: 1cm 2cm 1.3cm 4cm;
}

@font-face {
  font-family: Chunkfive; src: url('Chunkfive.otf');
}

div.text,
#content,
li[lang=ru] {
  font: Tahoma, Chunkfive, sans-serif;
  background: url('hatch.png') /* wtf? */;  color: #F0F0F0 !important;
  width: 100%;
}
```

## D

```d
#!/usr/bin/rdmd
// Computes average line length for standard input.
import std.stdio;

/+
  this is a /+ nesting +/ comment
+/

enum COMPILED_ON = __TIMESTAMP__;  // special token

enum character = '©';
enum copy_valid = '&copy;';
enum backslash_escaped = '\\';

// string literals
enum str = `hello "world"!`;
enum multiline = r"lorem
ipsum
dolor";  // wysiwyg string, no escapes here allowed
enum multiline2 = "sit
amet
\"adipiscing\"
elit.";
enum hex = x"66 6f 6f";   // same as "foo"

#line 5

// float literals
enum f = [3.14f, .1, 1., 1e100, 0xc0de.01p+100];

static if (something == true) {
   import std.algorithm;
}

void main() pure nothrow @safe {
    ulong lines = 0;
    double sumLength = 0;
    foreach (line; stdin.byLine()) {
        ++lines;
        sumLength += line.length;
    }
    writeln("Average line length: ",
        lines ? sumLength / lines : 0);
}
```

## Dart

```dart
library app;
import 'dart:html';

part 'app2.dart';

/**
 * Class description and [link](http://dartlang.org/).
 */
@Awesome('it works!')
class SomeClass<S extends Iterable> extends BaseClass<S> implements Comparable {
  factory SomeClass(num param);
  SomeClass._internal(int q) : super() {
    assert(q != 1);
    double z = 0.0;
  }

  /// **Sum** function
  int sum(int a, int b) => a + b;

  ElementList els() => querySelectorAll('.dart');
}

String str = ' (${'parameter' + 'zxc'})';
String str = " (${true ? 2 + 2 / 2 : null})";
String str = r'\nraw\';
String str = r"\nraw\";
var str = '''
Something ${2+3}
''';
var str = r"""
Something ${2+3}
""";
```

## Delphi

```delphi
TList = Class(TObject)
Private
  Some: String;
Public
  Procedure Inside; // Suxx
End;{TList}

Procedure CopyFile(InFileName, var OutFileName: String);
Const
  BufSize = 4096; (* Huh? *)
Var
  InFile, OutFile: TStream;
  Buffer: Array[1..BufSize] Of Byte;
  ReadBufSize: Integer;
Begin
  InFile := Nil;
  OutFile := Nil;
  Try
    InFile := TFileStream.Create(InFileName, fmOpenRead);
    OutFile := TFileStream.Create(OutFileName, fmCreate);
    Repeat
      ReadBufSize := InFile.Read(Buffer, BufSize);
      OutFile.Write(Buffer, ReadBufSize);
    Until ReadBufSize<>BufSize;
    Log('File ''' + InFileName + ''' copied'#13#10);
  Finally
    InFile.Free;
    OutFile.Free;
  End;{Try}
End;{CopyFile}
```

## Diff

```diff
Index: languages/ini.js
===================================================================
--- languages/ini.js    (revision 199)
+++ languages/ini.js    (revision 200)
@@ -1,8 +1,7 @@
 hljs.LANGUAGES.ini =
 {
   case_insensitive: true,
-  defaultMode:
-  {
+  defaultMode: {
     contains: ['comment', 'title', 'setting'],
     illegal: '[^\\s]'
   },

*** /path/to/original timestamp
--- /path/to/new      timestamp
***************
*** 1,3 ****
--- 1,9 ----
+ This is an important
+ notice! It should
+ therefore be located at
+ the beginning of this
+ document!

! compress the size of the
! changes.

  It is important to spell
```

## Django

```django
{% if articles|length %}
{% for article in articles %}

{% custom %}

{# Striped table #}
<tr class="{% cycle odd,even %}">
  <td>{{ article|default:"Hi... " }}</td>
  <td {% if article.today %}class="today"{% endif %}>
    Published on {{ article.date }}
  </td>
</tr>

{% endfor %}
{% endif %}
```

## DNS Zone file

```dns
$ORIGIN example.com.    ; designates the start of this zone file in the namespace
$TTL 1h                 ; default expiration time of all resource records without their own TTL value
example.com.  IN  SOA   ns.example.com. username.example.com. ( 2007120710 1d 2h 4w 1h )
example.com.  IN  NS    ns                    ; ns.example.com is a nameserver for example.com
example.com.  IN  NS    ns.somewhere.example. ; ns.somewhere.example is a backup nameserver for example.com
example.com.  IN  MX    10 mail.example.com.  ; mail.example.com is the mailserver for example.com
@             IN  MX    20 mail2.example.com. ; equivalent to above line, "@" represents zone origin
@             IN  MX    50 mail3              ; equivalent to above line, but using a relative host name
example.com.  IN  A     192.0.2.1             ; IPv4 address for example.com
              IN  AAAA  2001:db8:10::1        ; IPv6 address for example.com
ns            IN  A     192.0.2.2             ; IPv4 address for ns.example.com
              IN  AAAA  2001:db8:10::2        ; IPv6 address for ns.example.com
www           IN  CNAME example.com.          ; www.example.com is an alias for example.com
wwwtest       IN  CNAME www                   ; wwwtest.example.com is another alias for www.example.com
mail          IN  A     192.0.2.3             ; IPv4 address for mail.example.com
mail2         IN  A     192.0.2.4             ; IPv4 address for mail2.example.com
mail3         IN  A     192.0.2.5             ; IPv4 address for mail3.example.com
```

## Dockerfile

```dockerfile
# Example instructions from https://docs.docker.com/reference/builder/
FROM ubuntu:14.04

MAINTAINER example@example.com

ENV foo /bar
WORKDIR ${foo}   # WORKDIR /bar
ADD . $foo       # ADD . /bar
COPY \$foo /quux # COPY $foo /quux

RUN apt-get update && apt-get install -y software-properties-common\
    zsh curl wget git htop\
    unzip vim telnet
RUN ["/bin/bash", "-c", "echo hello ${USER}"]

CMD ["executable","param1","param2"]
CMD command param1 param2

EXPOSE 1337

ENV myName="John Doe" myDog=Rex\ The\ Dog \
    myCat=fluffy

ENV myName John Doe
ENV myDog Rex The Dog
ENV myCat fluffy

ADD hom* /mydir/        # adds all files starting with "hom"
ADD hom?.txt /mydir/    # ? is replaced with any single character

COPY hom* /mydir/        # adds all files starting with "hom"
COPY hom?.txt /mydir/    # ? is replaced with any single character

ENTRYPOINT ["executable", "param1", "param2"]
ENTRYPOINT command param1 param2

VOLUME ["/data"]

USER daemon

LABEL com.example.label-with-value="foo"
LABEL version="1.0"
LABEL description="This text illustrates \
that label-values can span multiple lines."

WORKDIR /path/to/workdir

ONBUILD ADD . /app/src
```

## DOS .bat

```dos
cd \
copy a b
ping 192.168.0.1
@rem ping 192.168.0.1
net stop sharedaccess
del %tmp% /f /s /q
del %temp% /f /s /q
ipconfig /flushdns
taskkill /F /IM JAVA.EXE /T

cd Photoshop/Adobe Photoshop CS3/AMT/
if exist application.sif (
    ren application.sif _application.sif
) else (
    ren _application.sif application.sif
)

taskkill /F /IM proquota.exe /T

sfc /SCANNOW

set path = test

xcopy %1\*.* %2
```

## Dust

```dust
<h3>Hours</h3>

<ul>
  {#users}
  <li {hello}>{firstName}</li>{~n}
  {/users}
</ul>
```

## Elixir

```elixir
defrecord Person, first_name: nil, last_name: "Dudington" do
  def name record do # huh ?
    "#{record.first_name} #{record.last_name}"
  end
end

defrecord User, name: "José", age: 25

guy = Person.new first_name: "Guy"
guy.name

defmodule ListServer do
  @moduledoc """
  This module provides an easy to use ListServer, useful for keeping
  lists of things.
  """
  use GenServer.Behaviour
  alias Foo.Bar

  ### Public API
  @doc """
  Starts and links a new ListServer, returning {:ok, pid}

  ## Example

    iex> {:ok, pid} = ListServer.start_link

  """
  def start_link do
    :gen_server.start_link({:local, :list}, __MODULE__, [], [])
  end

  ### GenServer API
  def init(list) do
    {:ok, list}
  end

  # Clear the list
  def handle_cast :clear, list do
    {:noreply, []}
  end
end

{:ok, pid} = ListServer.start_link
pid <- {:foo, "bar"}

greeter = fn(x) -> IO.puts "hey #{x}" end
greeter.("Bob")

```

## Elm

```elm
module Examples.Hello (main, Point, Tree(..)) where

import Html exposing (Html, span, text)
import Html.Attributes exposing (..)
import Time

main : Html
main =
  span [class "welcome-message"] [text "Hello, World!"]

type alias Point = { x : Int, y : Int }

type Tree a = Leaf a | Node (Tree a) a (Tree a)

flatten : Tree a -> List a
flatten t =
  case t of
    Leaf a -> [a]
    Node l a r -> flatten l ++ a :: flatten r

-- outgoing values
port time : Signal Float
port time = Time.every 1000
```

## ERB (Embedded Ruby)

```erb
<%# this is a comment %>

<% @posts.each do |post| %>
  <p><%= link_to post.title, post %></p>
<% end %>

<%- available_things = things.select(&:available?) -%>
<%%- x = 1 + 2 -%%>
<%% value = 'real string #{@value}' %%>
<%%= available_things.inspect %%>
```

## Erlang REPL

```erlang-repl
1> Str = "abcd".
"abcd"
2> L = test:length(Str).
4
3> Descriptor = {L, list_to_atom(Str)}.
{4,abcd}
4> L.
4
5> b().
Descriptor = {4,abcd}
L = 4
Str = "abcd"
ok
6> f(L).
ok
7> b().
Descriptor = {4,abcd}
Str = "abcd"
ok
8> {L, _} = Descriptor.
{4,abcd}
9> L.
4
10> 2#101.
5
11> 1.85e+3.
1850
```

## Erlang

```erlang
-module(ssh_cli).

-behaviour(ssh_channel).

-include("ssh.hrl").
%% backwards compatibility
-export([listen/1, listen/2, listen/3, listen/4, stop/1]).

if L =/= [] ->      % If L is not empty
    sum(L) / count(L);
true ->
    error
end.

%% state
-record(state, {
    cm,
    channel
   }).

-spec foo(integer()) -> integer().
foo(X) -> 1 + X.

test(Foo)->Foo.

init([Shell, Exec]) ->
    {ok, #state{shell = Shell, exec = Exec}};
init([Shell]) ->
    false = not true,
    io:format("Hello, \"~p!~n", [atom_to_list('World')]),
    {ok, #state{shell = Shell}}.

concat([Single]) -> Single;
concat(RList) ->
    EpsilonFree = lists:filter(
        fun (Element) ->
            case Element of
                epsilon -> false;
                _ -> true
            end
        end,
        RList),
    case EpsilonFree of
        [Single] -> Single;
        Other -> {concat, Other}
    end.

union_dot_union({union, _}=U1, {union, _}=U2) ->
    union(lists:flatten(
        lists:map(
            fun (X1) ->
                lists:map(
                    fun (X2) ->
                        concat([X1, X2])
                    end,
                    union_to_list(U2)
                )
            end,
            union_to_list(U1)
        ))).
```

## FIX

```fix
8=FIX.4.2␁9=0␁35=8␁49=SENDERTEST␁56=TARGETTEST␁34=00000001526␁52=20120429-13:30:08.137␁1=ABC12345␁11=2012abc1234␁14=100␁17=201254321␁20=0␁30=NYSE␁31=108.20␁32=100␁38=100␁39=2␁40=1␁47=A␁54=5␁55=BRK␁59=2␁60=20120429-13:30:08.000␁65=B␁76=BROKER␁84=0␁100=NYSE␁111=100␁150=2␁151=0␁167=CS␁377=N␁10000=SampleCustomTag␁10=123␁

8=FIX.4.29=035=849=SENDERTEST56=TARGETTEST34=0000000152652=20120429-13:30:08.1371=ABC1234511=2012abc123414=10017=20125432120=030=NYSE31=108.2032=10038=10039=240=147=A54=555=BRK59=260=20120429-13:30:08.00065=B76=BROKER84=0100=NYSE111=100150=2151=0167=CS377=N10000=SampleCustomTag10=123

```

## Fortran

```fortran
subroutine test_sub(k)
    implicit none

  !===============================
  !   This is a test subroutine
  !===============================

    integer, intent(in)           :: k
    double precision, allocatable :: a(:)
    integer, parameter            :: nmax=10
    integer                       :: i

    allocate (a(nmax))

    do i=1,nmax
      a(i) = dble(i)*5.d0
    enddo

    print *, 'Hello world'
    write (*,*) a(:)

end subroutine test_sub
```

## F#

```fsharp
open System

// Single line comment...
(*
  This is a
  multiline comment.
*)
let checkList alist =
    match alist with
    | [] -> 0
    | [a] -> 1
    | [a; b] -> 2
    | [a; b; c] -> 3
    | _ -> failwith "List is too big!"


let text = "Some text..."
let text2 = @"A ""verbatim"" string..."
let catalog = """
Some "long" string...
"""

let rec fib x = if x <= 2 then 1 else fib(x-1) + fib(x-2)

let fibs =
    Async.Parallel [ for i in 0..40 -> async { return fib(i) } ]
    |> Async.RunSynchronously

type Sprocket(gears) =
  member this.Gears : int = gears

[<AbstractClass>]
type Animal =
  abstract Speak : unit -> unit

type Widget =
  | RedWidget
  | GreenWidget

type Point = {X: float; Y: float;}

[<Measure>]
type s
let minutte = 60<s>

type DefaultMailbox<'a>() =
    let mutable inbox = ConcurrentQueue<'a>()
    let awaitMsg = new AutoResetEvent(false)
```

## GAMS

```gams
SETS
    I   canning plants   / SEATTLE, SAN-DIEGO /
    J   markets          / NEW-YORK, CHICAGO, TOPEKA / ;
PARAMETERS
    A(I)  capacity of plant i in cases
      /    SEATTLE     350
           SAN-DIEGO   600  /
    B(J)  demand at market j in cases
      /    NEW-YORK    325
           CHICAGO     300
           TOPEKA      275  / ;
TABLE D(I,J)  distance in thousands of miles
    NEW-YORK       CHICAGO      TOPEKA
    SEATTLE          2.5           1.7          1.8
    SAN-DIEGO        2.5           1.8          1.4  ;
SCALAR F  freight in dollars per case per thousand miles  /90/ ;
```

## G-code (ISO 6983)

```gcode
O003 (DIAMOND SQUARE)
N2 G54 G90 G49 G80
N3 M6 T1 (1.ENDMILL)
N4 M3 S1800
N5 G0 X-.6 Y2.050
N6 G43  H1  Z.1
N7 G1 Z-.3 F50.
N8 G41 D1 Y1.45
N9 G1 X0 F20.
N10 G2 J-1.45
(CUTTER COMP CANCEL)
N11 G1 Z-.2 F50.
N12 Y-.990
N13 G40
N14 G0 X-.6 Y1.590
N15 G0 Z.1
N16 M5 G49 G28 G91 Z0
N17 CALL O9456
N18 #500=0.004
N19 #503=[#500+#501]
N20 VC45=0.0006
VS4=0.0007
N21 G90 G10 L20 P3 X5.Y4. Z6.567
N22 G0 X5000
N23 IF [#1 LT 0.370] GOTO 49
N24 X-0.678 Y+.990
N25 G84.3 X-0.1
N26 #4=#5*COS[45]
N27 #4=#5*SIN[45]
N28 VZOFZ=652.9658
%
```

## Gherkin

```gherkin
# language: en
Feature: Addition
  In order to avoid silly mistakes
  As a math idiot
  I want to be told the sum of two numbers

  @this_is_a_tag
  Scenario Outline: Add two numbers
    * I have a calculator
    Given I have entered <input_1> into the calculator
    And I have entered <input_2> into the calculator
    When I press <button>
    Then the result should be <output> on the screen
    And I have a string like
    """
    Here is
    some
    multiline text
    """

  Examples:
    | input_1 | input_2 | button | output |
    | 20      | 30      | add    | 50     |
    | 2       | 5       | add    | 7      |
    | 0       | 40      | add    | 40     |
```

## GLSL

```glsl
// vertex shader
#version 150
in  vec2 in_Position;
in  vec3 in_Color;

out vec3 ex_Color;
void main(void) {
    gl_Position = vec4(in_Position.x, in_Position.y, 0.0, 1.0);
    ex_Color = in_Color;
}


// geometry shader
#version 150

layout(triangles) in;
layout(triangle_strip, max_vertices = 3) out;

void main() {
  for(int i = 0; i < gl_in.length(); i++) {
    gl_Position = gl_in[i].gl_Position;
    EmitVertex();
  }
  EndPrimitive();
}


// fragment shader
#version 150
precision highp float;

in  vec3 ex_Color;
out vec4 gl_FragColor;

void main(void) {
    gl_FragColor = vec4(ex_Color, 1.0);
}
```

## Go

```go
package main

import (
    "fmt"
    "os"
)

const (
    Sunday = iota
    numberOfDays  // this constant is not exported
)

type Foo interface {
    FooFunc(int, float32) (complex128, []int)
}

type Bar struct {
    os.File /* multi-line
               comment */
    PublicData chan int
}

func main() {
    ch := make(chan int)
    ch <- 1
    x, ok := <- ch
    ok = true
    float_var := 1.0e10
    defer fmt.Println('\'')
    defer fmt.Println(`exitting now\`)
    var fv1 float64 = 0.75
    go println(len("hello world!"))
    return
}
```

## Golo

```golo
module hello

function dyno = -> DynamicObject()

struct human = { name }

@annotated
function main = |args| {
    let a = 1
    var b = 2
    
    println("hello") 

    let john = human("John Doe")
}
```

## Gradle

```gradle

apply plugin: 'android'

android {
    compileSdkVersion 19
    buildToolsVersion "19.1"

    defaultConfig {
        minSdkVersion 15
        targetSdkVersion 19
        versionCode 5
        versionName "0.4.4"
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_7
        targetCompatibility JavaVersion.VERSION_1_7
    }
    signingConfigs {
        release
    }
    buildTypes {
        release {
            // runProguard true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.txt'
            signingConfig signingConfigs.release
        }
    }
}

dependencies {
    compile fileTree(dir: 'libs', include: ['*.jar'])

    compile 'com.example:example-lib:1.0.0'
}


def propFile = file('../signing.properties')
if( propFile.canRead() ) {
    def Properties p = new Properties()
    p.load(new FileInputStream(propFile))

    if( p!=null
    &&  p.containsKey("STORE_FILE")
    &&  p.containsKey('STORE_PASSWORD')
    &&  p.containsKey('KEY_ALIAS')
    &&  p.containsKey('KEY_PASSWORD')
    ) {
        println "RELEASE_BUILD: Signing..."

        android.signingConfigs.release.storeFile = file( p['STORE_FILE'] )
        android.signingConfigs.release.storePassword = p['STORE_PASSWORD']
        android.signingConfigs.release.keyAlias = p['KEY_ALIAS']
        android.signingConfigs.release.keyPassword = p['KEY_PASSWORD']
    } else {
        println "RELEASE_BUILD: Required properties in signing.properties are missing"
        android.buildTypes.release.signingConfig = null
    }
} else {
    println "RELEASE_BUILD: signing.properties not found"
    android.buildTypes.release.signingProperties = null
}
```

## Groovy

```groovy
#!/usr/bin/env groovy
package model

import groovy.transform.CompileStatic
import java.util.List as MyList

trait Distributable {
    void distribute(String version) {}
}

@CompileStatic
class Distribution implements Distributable {
    double number = 1234.234 / 567
    def otherNumber = 3 / 4
    boolean archivable = condition ?: true
    def ternary = a ? b : c
    String name = "Guillaume"
    Closure description = null
    List<DownloadPackage> packages = []
    String regex = ~/.*foo.*/
    String multi = '''
        multi line string
    ''' + """
        now with double quotes and ${gstring}
    """ + $/
        even with dollar slashy strings
    /$

    /**
     * description method
     * @param cl the closure
     */
    void description(Closure cl) { this.description = cl }

    void version(String name, Closure versionSpec) {
        def closure = { println "hi" } as Runnable

        MyList ml = [1, 2, [a: 1, b:2,c :3]]
        for (ch in "name") {}

        // single line comment
        DownloadPackage pkg = new DownloadPackage(version: name)

        check that: true

        label:
        def clone = versionSpec.rehydrate(pkg, pkg, pkg)
        /*
            now clone() in a multiline comment
        */
        clone()
        packages.add(pkg)

        assert 4 / 2 == 2
    }
}
```

## Haml

```haml
!!! XML
%html
  %body
    %h1.jumbo{:id=>"a", :style=>'font-weight: normal', :title=>title} highlight.js
    /html comment
    -# ignore this line
    %ul(style='margin: 0')
    -items.each do |i|
      %i= i
    = variable
    =variable2
    ~ variable3
    ~variable4
    The current year is #{DataTime.now.year}.
```

## Handlebars

```handlebars
<div class="entry">
  {{!-- only output this author names if an author exists --}}
  {{#if author}}
    <h1>{{firstName}} {{lastName}}</h1>
  {{/if}}
</div>
```

## Haskell

```haskell
{-# LANGUAGE TypeSynonymInstances #-}
module Network.UDP
( DataPacket(..)
, openBoundUDPPort
, openListeningUDPPort
, pingUDPPort
, sendUDPPacketTo
, recvUDPPacket
, recvUDPPacketFrom
) where

import qualified Data.ByteString as Strict (ByteString, concat, singleton)
import qualified Data.ByteString.Lazy as Lazy (ByteString, toChunks, fromChunks)
import Data.ByteString.Char8 (pack, unpack)
import Network.Socket hiding (sendTo, recv, recvFrom)
import Network.Socket.ByteString (sendTo, recv, recvFrom)

-- Type class for converting StringLike types to and from strict ByteStrings
class DataPacket a where
  toStrictBS :: a -> Strict.ByteString
  fromStrictBS :: Strict.ByteString -> a

instance DataPacket Strict.ByteString where
  toStrictBS = id
  {-# INLINE toStrictBS #-}
  fromStrictBS = id
  {-# INLINE fromStrictBS #-}

openBoundUDPPort :: String -> Int -> IO Socket
openBoundUDPPort uri port = do
  s <- getUDPSocket
  bindAddr <- inet_addr uri
  let a = SockAddrInet (toEnum port) bindAddr
  bindSocket s a
  return s

pingUDPPort :: Socket -> SockAddr -> IO ()
pingUDPPort s a = sendTo s (Strict.singleton 0) a >> return ()
```

## Haxe

```haxe

// quicksort example from http://haxe.org/doc/snip/quicksort
class Quicksort {

    static var arr = [4,8,0,3,9,1,5,2,6,7];

    static function quicksort( lo : Int, hi : Int ) : Void {
        var i = lo;
        var j = hi;
        var buf = arr;
        var p = buf[(lo+hi)>>1];
        while( i <= j ) {
            while( arr[i] > p ) i++;
            while( arr[j] < p ) j--;
            if( i <= j ) {
                var t = buf[i];
                buf[i++] = buf[j];
                buf[j--] = t;
            }
        }
        if( lo < j ) quicksort( lo, j );
        if( i < hi ) quicksort( i, hi );
    }

    static function main() {
        quicksort( 0, arr.length-1 );
        trace(arr);
    }
}
```

## HTTP

```http
POST /task?id=1 HTTP/1.1
Host: example.org
Content-Type: application/json; charset=utf-8
Content-Length: 19

{"status": "ok", "extended": true}
```

## Inform 7

```inform7
Book 1 - Language Definition Testing File

[Comments in Inform 7 can be [nested] inside one another]

Syntax highlighting is an action applying to one thing.
Understand "highlight [something preferably codeish]" as syntax highlighting.

Code is a kind of thing. Code is usually plural-named.

Code can be highlighted. Code is usually not highlighted.

Check syntax highlighting:
  unless the noun is code:
    say "[The noun] isn't source code you can highlight.";
    rule fails.

Carry out syntax highlighting:
  now the noun is highlighted.

Table of Programming Languages
language  utility
ruby      "Web back-end development"
lua       "Embedded scripting"
erlang    "High-concurrency server applications"
```

## Ini

```ini
; boilerplate
[package]
name = "some_name"
authors = ["Author"]
description = "This is \
a description"

[[lib]]
name = ${NAME}
default = True
auto = no
counter = 1_000
```

## IRPF90

```irpf90
 BEGIN_PROVIDER [ integer(bit_kind), psi_det_sorted_bit, (N_int,2,psi_det_size) ]
&BEGIN_PROVIDER [ double precision, psi_coef_sorted_bit, (psi_det_size,N_states) ]
 implicit none
 BEGIN_DOC
 ! Determinants on which we apply <i|H|psi> for perturbation.
 ! They are sorted by determinants interpreted as integers. Useful
 ! to accelerate the search of a random determinant in the wave
 ! function.
 END_DOC
 integer :: i,j,k
 integer, allocatable ::  iorder(:)
 integer*8, allocatable :: bit_tmp(:)
 integer*8, external :: det_search_key

 allocate ( iorder(N_det), bit_tmp(N_det) )

 do i=1,N_det
   iorder(i) = i
   !DIR$ FORCEINLINE
   bit_tmp(i) = det_search_key(psi_det(1,1,i),N_int)
 enddo
 call isort(bit_tmp,iorder,N_det)
 !DIR$ IVDEP
 do i=1,N_det
  do j=1,N_int
    psi_det_sorted_bit(j,1,i) = psi_det(j,1,iorder(i))
    psi_det_sorted_bit(j,2,i) = psi_det(j,2,iorder(i))
  enddo
  do k=1,N_states
    psi_coef_sorted_bit(i,k) = psi_coef(iorder(i),k)
  enddo
 enddo

 deallocate(iorder, bit_tmp)

END_PROVIDER

```

## Java

```java
/**
 * @author John Smith <john.smith@example.com>
 * @version 1.0
*/
package l2f.gameserver.model;

import java.util.ArrayList;

public abstract class L2Character extends L2Object {
  public static final Short ABNORMAL_EFFECT_BLEEDING = 0x0_0_0_1; // not sure

  public void moveTo(int x, int y, int z) {
    _ai = null;
    _log.warning("Should not be called");
    if (1 > 5) {
      return;
    }
  }

  /** Task of AI notification */
  @SuppressWarnings( { "nls", "unqualified-field-access", "boxing" })
  public class NotifyAITask implements Runnable {
    private final CtrlEvent _evt;

    List<String> mList = new ArrayList<String>()

    public void run() {
      try {
        getAI().notifyEvent(_evt, _evt.class, null);
      } catch (Throwable t) {
        t.printStackTrace();
      }
    }
  }
}
```

## JavaScript

```javascript
import {x, y} as p from 'point';
const ANSWER = 42;

class Car extends Vehicle {
  constructor(speed, cost) {
    super(speed);

    var c = Symbol('cost');
    this[c] = cost;

    this.intro = `This is a car runs at
      ${speed}.`;
  }
}

for (let num of [1, 2, 3]) {
  console.log(num + 0b111110111);
}

function $initHighlight(block, flags) {
  try {
    if (block.className.search(/\bno\-highlight\b/) != -1)
      return processBlock(block.function, true, 0x0F) + ' class=""';
  } catch (e) {
    /* handle exception */
    var e4x =
        <div>Example
            <p>1234</p></div>;
  }
  for (var i = 0 / 2; i < classes.length; i++) { // "0 / 2" should not be parsed as regexp
    if (checkCondition(classes[i]) === undefined)
      return /\d+[\s/]/g;
  }
  console.log(Array.every(classes, Boolean));
}

export  $initHighlight;
```

## JSON

```json
[
  {
    "title": "apples",
    "count": [12000, 20000],
    "description": {"text": "...", "sensitive": false}
  },
  {
    "title": "oranges",
    "count": [17500, null],
    "description": {"text": "...", "sensitive": false}
  }
]
```

## Julia

```julia
using Profile

# type definition
immutable Point{T<:FloatingPoint}
    index::Int
    x::T
    y::T
end

#=
Multi
Line
Comment
=#
function method0(x, y::Int; version::VersionNumber=v"0.1.2")
    """
    Triple
    Quoted
    String
    """

    @assert π > e

    s = 1.2
    変数 = "variable"

    if s * 100_000 ≥ 5.2e+10 && true || is(x, nothing)
        s = 1. + .5im
    elseif 1 ∈ [1, 2, 3]
        println("s is $s and 変数 is $変数")
    else
        x = [1 2 3; 4 5 6]
        @show x'
    end

    local var = rand(10)
    var[1:5]
    var[5:end-1]
    var[end]

    opt = "-la"
    run(`ls $opt`)

    '\u2200' != 'T'

    return 5s / 2
end
```

## Kotlin

```kotlin
import kotlin.lang.test

trait A {
    fun x()
}

fun xxx() : Int {
	return 888
}

public fun main(args : Array<String>) {
}
```

## Lasso

```lasso
<?LassoScript
/* Lasso 8 */
  local('query' = 'SELECT * FROM `'+var:'table'+'` WHERE `id` > 10
    ORDER BY `Name` LIMIT 30');
  Inline: -Username=$DBuser, -Password=$DBpass, -Database=$DBname, -sql=#query;
    var("class1.name" = (found_count != 0 ? "subtotal" | "nonefound"),
        "total_amount" = found_count || "No results");
    records;
      output: "<tr>"loop_count"</tr>";
    /records;
  /Inline;
?><div class="[$class1.name]">[$total_amount]</div>
<?lasso
/* Lasso 9 */ ?>
[noprocess] causes [delimiters] to be <?=skipped?> until the next [/noprocess]
[
  define strings_combine(value::string, ...other)::string => {
    local(result = #value->append(#other->asString&trim))
    return set(#result, not #other, \givenBlock)
  }
  /**! descriptive text */
  define person => type {
    parent entity
    data name::string, protected nickname, birthdate :: date
    data private ssn = null
    private showAge() => { return ..age }
    protected fullName() => `"` + .nickname + `"` + .'name'
    public ssnListed::boolean => .ssn() ? true | false
  }
  define person->name=(value) => {
    .'name' = #value
    return self->'name'
  }
] <!-- an HTML comment <?=disables delimiters?> as well -->
[no_square_brackets] disables [square brackets] for the rest of the file
<?=
  // query expression
  with n in array((:-12, 0xABCD, 3.14159e14), (:NaN, -infinity, .57721))
  let swapped = pair(#n->\second, #n->first)
  group #swapped by #n->first into t
  let key = #t->key
  order by #key
  select pair(#key, #1)
  do {^
    #n->upperCase
  ^}
?>
```

## Less

```less
/*
Using the most minimal language subset to ensure we
have enough relevance hints for proper Less detection
*/

@import "fruits";

@rhythm: 1.5em;

@media screen and (min-resolution: 2dppx) {
    body {font-size: 125%}
}

section > .foo + #bar:hover [href*="less"] {
    margin:     @rhythm 0 0 @rhythm;
    padding:    calc(5% + 20px);
    background: #f00ba7 url(http://placehold.alpha-centauri/42.png) no-repeat;
    background-image: linear-gradient(-135deg, wheat, fuchsia) !important ;
    background-blend-mode: multiply;
}

@font-face {
    font-family: /* ? */ 'Omega';
    src: url('../fonts/omega-webfont.woff?v=2.0.2');
}

.icon-baz::before {
    display:     inline-block;
    font-family: "Omega", Alpha, sans-serif;
    content:     "\f085";
    color:       rgba(98, 76 /* or 54 */, 231, .75);
}
```

## Lisp

```lisp
#!/usr/bin/env csi

(defun prompt-for-cd ()
   "Prompts
    for CD"
   (prompt-read "Title" 1.53 1 2/4 1.7 1.7e0 2.9E-4 +42 -7 #b001 #b001/100 #o777 #O777 #xabc55 #c(0 -5.6))
   (prompt-read "Artist" &rest)
   (or (parse-integer (prompt-read "Rating") :junk-allowed t) 0)
  (if x (format t "yes") (format t "no" nil) ;and here comment
  )
  ;; second line comment
  '(+ 1 2)
  (defvar *lines*)                ; list of all lines
  (position-if-not #'sys::whitespacep line :start beg))
  (quote (privet 1 2 3))
  '(hello world)
  (* 5 7)
  (1 2 34 5)
  (:use "aaaa")
  (let ((x 10) (y 20))
    (print (+ x y))
  )
```

## LiveCode

```livecodeserver
<?rev

global gControllerHandlers, gData
local sTest
put "blog,index" into gControllerHandlers


command blog
  -- simple comment
  put "Hello World!" into sTest
  # ANOTHER COMMENT
  put "form,url,asset" into tHelpers
  rigLoadHelper tHelpers
end blog

/*Hello
block comment!*/

function myFunction
  if the secs > 2000000000 then
    put "Welcome to the future!"
  else
    return "something"
  end if
end myFunction


--| END OF blog.lc
--| Location: ./system/application/controllers/blog.lc
----------------------------------------------------------------------
```

## LiveScript

```livescript
# take the first n objects from a list
take = (n, [x, ...xs]:list) -->
  | n <= 0     => []
  | empty list => []
  | otherwise  => [x] ++ take n - 1, xs

take 2, [1, 2, 3, 4, 5]

# Curried functions
take-three = take 3
take-three [6, 7, 8, 9, 10]

# Function composition
last-three = reverse >> take-three >> reverse
last-three [1 to 8]

# List comprehensions and piping
t1 =
  * id: 1
    name: 'george'
  * id: 2
    name: 'mike'
  * id: 3
    name: 'donald'

t2 =
  * id: 2
    age: 21
  * id: 1
    age: 20
  * id: 3
    age: 26
[{id:id1, name, age}
  for {id:id1, name} in t1
  for {id:id2, age} in t2
  where id1 is id2]
  |> sort-by \id
  |> JSON.stringify
```

## Lua

```lua
--[[
Simple signal/slot implementation
]]
local signal_mt = {
    __index = {
        register = table.insert
    }
}
function signal_mt.__index:emit(... --[[ Comment in params ]])
    for _, slot in ipairs(self) do
        slot(self, ...)
    end
end
local function create_signal()
    return setmetatable({}, signal_mt)
end

-- Signal test
local signal = create_signal()
signal:register(function(signal, ...)
    print(...)
end)
signal:emit('Answer to Life, the Universe, and Everything:', 42)

--[==[ [=[ [[
Nested ]]
multi-line ]=]
comment ]==]
[==[ Nested
[=[ multi-line
[[ string
]] ]=] ]==]
```

## Makefile

```makefile
# Makefile

BUILDDIR      = _build
EXTRAS       ?= $(BUILDDIR)/extras

.PHONY: main clean

main:
	@echo "Building main facility..."
	build_main $(BUILDDIR)

clean:
	rm -rf $(BUILDDIR)/*
```

## Markdown

```markdown
# hello world

you can write text [with links](http://example.com) inline or [link references][1].

* one _thing_ has *em*phasis
* two __things__ are **bold**

[1]: http://example.com

---

hello world
===========

<this_is inline="xml"></this_is>

> markdown is so cool

    so are code segments

1. one thing (yeah!)
2. two thing `i can write code`, and `more` wipee!

```

## Mathematica

```mathematica
(* ::Package:: *)

(* Mathematica Package *)

BeginPackage["SomePkg`"]

Begin["`Private`"]

SomeFn[ns_List] := Fold[Function[{x, y}, x + y], 0, Map[# * 2 &, ns]];
Print[$ActivationKey];

End[] (* End Private Context *)

EndPackage[]
```

## Matlab

```matlab
n = 20; % number of points
points = [random('unid', 100, n, 1), random('unid', 100, n, 1)];
len = zeros(1, n - 1);
points = sortrows(points);
%% Initial set of points
plot(points(:,1),points(:,2));
for i = 1: n-1
    len(i) = points(i + 1, 1) - points(i, 1);
end
while(max(len) > 2 * min(len))
    [d, i] = max(len);
    k = on_margin(points, i, d, -1);
    m = on_margin(points, i + 1, d, 1);
    xm = 0; ym = 0;
%% New point
    if(i == 1 || i + 1 == n)
        xm = mean(points([i,i+1],1))
        ym = mean(points([i,i+1],2))
    else
        [xm, ym] = dlg1(points([k, i, i + 1, m], 1), ...
            points([k, i, i + 1, m], 2))
    end

    points = [ points(1:i, :); [xm, ym]; points(i + 1:end, :)];
end

%{
    This is a block comment. Please ignore me.
%}

function [net] = get_fit_network(inputs, targets)
    % Create Network
    numHiddenNeurons = 20;  % Adjust as desired
    net = newfit(inputs,targets,numHiddenNeurons);
    net.trainParam.goal = 0.01;
    net.trainParam.epochs = 1000;
    % Train and Apply Network
    [net,tr] = train(net,inputs,targets);
end

foo_matrix = [1, 2, 3; 4, 5, 6]''';
foo_cell = {1, 2, 3; 4, 5, 6}''.'.';

cell2flatten = {1,2,3,4,5};
flattenedcell = cat(1, cell2flatten{:});
```

## MEL

```mel
proc string[] getSelectedLights()

{
  string $selectedLights[];

  string $select[] = `ls -sl -dag -leaf`;

  for ( $shape in $select )
  {
    // Determine if this is a light.
    //
    string $class[] = getClassification( `nodeType $shape` );


    if ( ( `size $class` ) > 0 && ( "light" == $class[0] ) )
    {
      $selectedLights[ `size $selectedLights` ] = $shape;
    }
  }

  // Result is an array of all lights included in

  // current selection list.
  return $selectedLights;
}
```

## Mercury

```mercury
% "Hello World" in Mercury.
:- module hello.


:- interface.
:- import_module io.

:- pred main(io::di, io::uo) is det.


:- implementation.

main(!IO) :-
    io.write_string("Hello, world\n", !IO).

:- pred filter(pred(T), list(T), list(T), list(T) ).
:- mode filter(in(pred(in) is semidet), in, out, out ) is det.

filter(_, [], [], []).
filter(P, [X | Xs], Ys, Zs) :-
    filter(P, Xs, Ys0, Zs0),
    ( if P(X)   then    Ys = [X | Ys0],   Zs = Zs0
                else    Ys = Ys0      ,   Zs = [X | Zs0]
    ).
```

## Mizar

```mizar
::: ## Lambda calculus

environ

  vocabularies LAMBDA,
      NUMBERS,
      NAT_1, XBOOLE_0, SUBSET_1, FINSEQ_1, XXREAL_0, CARD_1,
      ARYTM_1, ARYTM_3, TARSKI, RELAT_1, ORDINAL4, FUNCOP_1;

  :: etc...

begin

reserve D for DecoratedTree,
        p,q,r for FinSequence of NAT,
        x for set;

definition
  let D;

  attr D is LambdaTerm-like means
    (dom D qua Tree) is finite &
::>                          *143,306
    for r st r in dom D holds
      r is FinSequence of {0,1} &
      r^<*0*> in dom D implies D.r = 0;
end;

registration
  cluster LambdaTerm-like for DecoratedTree of NAT;
  existence;
::>       *4
end;

definition
  mode LambdaTerm is LambdaTerm-like DecoratedTree of NAT;
end;

::: Then we extend this ordinary one-step beta reduction, that is,
:::  any subterm is also allowed to reduce.
definition
  let M,N;

  pred M beta N means
    ex p st
      M|p beta_shallow N|p &
      for q st not p is_a_prefix_of q holds
        [r,x] in M iff [r,x] in N;
end;

theorem Th4:
  ProperPrefixes (v^<*x*>) = ProperPrefixes v \/ {v}
proof
  thus ProperPrefixes (v^<*x*>) c= ProperPrefixes v \/ {v}
  proof
    let y;
    assume y in ProperPrefixes (v^<*x*>);
    then consider v1 such that
A1: y = v1 and
A2: v1 is_a_proper_prefix_of v^<*x*> by TREES_1:def 2;
 v1 is_a_prefix_of v & v1 <> v or v1 = v by A2,TREES_1:9;
then
 v1 is_a_proper_prefix_of v or v1 in {v} by TARSKI:def 1,XBOOLE_0:def 8;
then  y in ProperPrefixes v or y in {v} by A1,TREES_1:def 2;
    hence thesis by XBOOLE_0:def 3;
  end;
  let y;
  assume y in ProperPrefixes v \/ {v};
then A3: y in ProperPrefixes v or y in {v} by XBOOLE_0:def 3;
A4: now
    assume y in ProperPrefixes v;
    then consider v1 such that
A5: y = v1 and
A6: v1 is_a_proper_prefix_of v by TREES_1:def 2;
 v is_a_prefix_of v^<*x*> by TREES_1:1;
then  v1 is_a_proper_prefix_of v^<*x*> by A6,XBOOLE_1:58;
    hence thesis by A5,TREES_1:def 2;
  end;
 v^{} = v by FINSEQ_1:34;
  then
 v is_a_prefix_of v^<*x*> & v <> v^<*x*> by FINSEQ_1:33,TREES_1:1;
then  v is_a_proper_prefix_of v^<*x*> by XBOOLE_0:def 8;
then  y in ProperPrefixes v or y = v & v in ProperPrefixes (v^<*x*>)
  by A3,TARSKI:def 1,TREES_1:def 2;
  hence thesis by A4;
end;
```

## Mojolicious

```mojolicious
%layout 'bootstrap';
% title "Import your subs";
%= form_for '/settings/import' => (method => 'post', enctype => 'multipart/form-data') => begin
     %= file_field 'opmlfile' => multiple => 'true'
     %= submit_button 'Import', 'class' => 'btn'
% end
<div>
% if ($subs) {
<dl>
% for my $item (@$subs) {
% my ($dir, $align) = ($item->{rtl}) ? ('rtl', 'right') : ('ltr', 'left');
<dt align="<%= $align %>"><a href="<%= $item->{'xmlUrl'} %>"><i class="icon-rss"></i> rss</a>
<a dir="<%= $dir %>" href="<%= $item->{htmlUrl} %>"><%== $item->{title} %></a>
</dt>
<dd><b>Categories</b>
%= join q{, }, sort @{ $item->{categories} || [] };
</dd>
</dl>
% }
</div>
```

## Monkey

```monkey
#IMAGE_FILES="*.png|*.jpg"
#SOUND_FILES="*.wav|*.ogg"
#MUSIC_FILES="*.wav|*.ogg"
#BINARY_FILES="*.bin|*.dat"

Import mojo

' The main class which expends Mojo's 'App' class:
Class GameApp Extends App
    Field player:Player

    Method OnCreate:Int()
        Local img:Image = LoadImage("player.png")
        Self.player = New Player()
        SetUpdateRate(60)

        Return 0
    End

    Method OnUpdate:Int()
        player.x += HALFPI

        If (player.x > 100) Then
            player.x = 0
        Endif

        Return 0
    End

    Method OnRender:Int()
        Cls(32, 64, 128)
        player.Draw()

        player = Null
        Return 0
    End
End
```

## Nginx

```nginx
user  www www;
worker_processes  2;
pid /var/run/nginx.pid;
error_log  /var/log/nginx.error_log  debug | info | notice | warn | error | crit;

events {
    connections   2000;
    use kqueue | rtsig | epoll | /dev/poll | select | poll;
}

http {
    log_format main      '$remote_addr - $remote_user [$time_local] '
                         '"$request" $status $bytes_sent '
                         '"$http_referer" "$http_user_agent" '
                         '"$gzip_ratio"';

    send_timeout 3m;
    client_header_buffer_size 1k;

    gzip on;
    gzip_min_length 1100;

    #lingering_time 30;

    server {
        server_name   one.example.com  www.one.example.com;
        access_log   /var/log/nginx.access_log  main;

        rewrite (.*) /index.php?page=$1 break;

        location / {
            proxy_pass         http://127.0.0.1/;
            proxy_redirect     off;
            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            charset            koi8-r;
        }

        location /api/ {
            fastcgi_pass 127.0.0.1:9000;
        }

        location ~* \.(jpg|jpeg|gif)$ {
            root         /spool/www;
        }
    }
}
```

## Nimrod

```nimrod
import module1, module2, module3
from module4 import nil

type
  TFoo = object ## Doc comment
    a: int32
  PFoo = ref TFoo

proc do_stuff314(param_1: TFoo, par2am: var PFoo): PFoo {.exportc: "dostuff" .} =
  # Regular comment
  discard """
  dfag
sdfg""
"""
  result = nil

method abc(a: TFoo) = discard 1u32 + 0xabcdefABCDEFi32 + 0o01234567i8 + 0b010

discard rawstring"asdf""adfa"
var normalstring = "asdf"
let a: uint32 = 0xFFaF'u32
```

## Nix

```nix
{ stdenv, foo, bar ? false, ... }:

/*
 * foo
 */

let
  a = 1; # just a comment
  b = null;
  c = toString 10;
in stdenv.mkDerivation rec {
  name = "foo-${version}";
  version = "1.3";

  configureFlags = [ "--with-foo2" ] ++ stdenv.lib.optional bar "--with-foo=${ with stdenv.lib; foo }"

  postInstall = ''
    ${ if true then "--${test}" else false }
  '';

  meta = with stdenv.lib; {
    homepage = https://nixos.org;
  };
}
```

## NSIS

```nsis
/*
  NSIS Scheme
  for highlight.js
*/

; Includes
!include MUI2.nsh

; Settings
Name "installer_name"
OutFile "installer_name.exe"
RequestExecutionLevel user
CRCCheck on
!ifdef x64
  InstallDir "$PROGRAMFILES64\installer_name"
!else
  InstallDir "$PROGRAMFILES\installer_name"
!endif

; Pages
!insertmacro MUI_PAGE_INSTFILES

; Sections
Section "section_name" section_index
  # your code here
SectionEnd

; Functions
Function .onInit

  MessageBox MB_OK "Here comes a$\n$\rline-break!"

FunctionEnd
```

## Objective C

```objective-c
#import <UIKit/UIKit.h>
#import "Dependency.h"

@protocol WorldDataSource
@optional
- (NSString*)worldName;
@required
- (BOOL)allowsToLive;
@end

@interface Test : NSObject <HelloDelegate, WorldDataSource> {
  NSString *_greeting;
}

@property (nonatomic, readonly) NSString *greeting;
- (IBAction) show;
@end

@implementation Test

@synthesize test=_test;

+ (id) test {
  return [self testWithGreeting:@"Hello, world!\nFoo bar!"];
}

+ (id) testWithGreeting:(NSString*)greeting {
  return [[[self alloc] initWithGreeting:greeting] autorelease];
}

- (id) initWithGreeting:(NSString*)greeting {
  if ( (self = [super init]) ) {
    _greeting = [greeting retain];
  }
  return self;
}

- (void) dealloc {
  [_greeting release];
  [super dealloc];
}

@end
```

## OCaml

```ocaml
(* This is a
multiline, (* nested *) comment *)
type point = { x: float; y: float };;
let some_string = "this is a string";;
let rec length lst =
    match lst with
      [] -> 0
    | head :: tail -> 1 + length tail
  ;;
exception Test;;
type expression =
      Const of float
    | Var of string
    | Sum of expression * expression    (* e1 + e2 *)
    | Diff of expression * expression   (* e1 - e2 *)
    | Prod of expression * expression   (* e1 * e2 *)
    | Quot of expression * expression   (* e1 / e2 *)
class point =
    object
      val mutable x = 0
      method get_x = x
      method private move d = x <- x + d
    end;;
```

## OpenSCAD

```openscad
use <write.scad>
include <../common/base.scad>

//draw a foobar
module foobar(){
    translate([0,-10,0])
    difference(){
        cube([5,10.04,15]);
        sphere(r=10,$fn=100);
    }
}

foobar();
#cube ([5,5,5]);
echo("done");
```

## Oxygene

```oxygene
namespace LinkedList;

interface

uses
  System.Text;

type
  List<T> = public class
    where T is Object;
  private
    method AppendToString(aBuilder: StringBuilder);
  public
    constructor(aData: T);
    constructor(aData: T; aNext: List<T>);
    property Next: List<T>;
    property Data: T;

    method ToString: string; override;
  end;

implementation

constructor List<T>(aData: T);
begin
  Data := aData;
end;

constructor List<T>(aData: T; aNext: List<T>);
begin
  constructor(aData);
  Next := aNext;
end;

method List<T>.ToString: string;
begin
  with lBuilder := new StringBuilder do begin
    AppendToString(lBuilder);
    result := lBuilder.ToString();
  end;
end;

method List<T>.AppendToString(aBuilder: StringBuilder);
begin
  if assigned(Data) then
    aBuilder.Append(Data.ToString)
  else
    aBuilder.Append('nil');

  if assigned(Next) then begin
    aBuilder.Append(', ');
    Next.AppendToString(aBuilder);
  end;
end;

end.
```

## Parser3

```parser3
@CLASS
base

@USE
module.p

@BASE
class

# Comment for code
@create[aParam1;aParam2][local1;local2]
  ^connect[mysql://host/database?ClientCharset=windows-1251]
  ^for[i](1;10){
    <p class="paragraph">^eval($i+10)</p>
    ^connect[mysql://host/database]{
      $tab[^table::sql{select * from `table` where a='1'}]
      $var_Name[some${value}]
    }
  }

  ^rem{
    Multiline comment with code: $var
    ^while(true){
      ^for[i](1;10){
        ^sleep[]
      }
    }
  }
  ^taint[^#0A]

@GET_base[]
## Comment for code
  # Isn't comment
  $result[$.hash_item1[one] $.hash_item2[two]]
```

## Perl

```perl
# loads object
sub load
{
  my $flds = $c->db_load($id,@_) || do {
    Carp::carp "Can`t load (class: $c, id: $id): '$!'"; return undef
  };
  my $o = $c->_perl_new();
  $id12 = $id / 24 / 3600;
  $o->{'ID'} = $id12 + 123;
  #$o->{'SHCUT'} = $flds->{'SHCUT'};
  my $p = $o->props;
  my $vt;
  $string =~ m/^sought_text$/;
  $items = split //, 'abc';
  $string //= "bar";
  for my $key (keys %$p)
  {
    if(${$vt.'::property'}) {
      $o->{$key . '_real'} = $flds->{$key};
      tie $o->{$key}, 'CMSBuilder::Property', $o, $key;
    }
  }
  $o->save if delete $o->{'_save_after_load'};

  # GH-117
  my $g = glob("/usr/bin/*");

  return $o;
}

__DATA__
@@ layouts/default.html.ep
<!DOCTYPE html>
<html>
  <head><title><%= title %></title></head>
  <body><%= content %></body>
</html>
__END__

=head1 NAME
POD till the end of file
```

## pf

```pf
# from the PF FAQ: http://www.openbsd.org/faq/pf/example1.html

# macros

int_if="xl0"

tcp_services="{ 22, 113 }"
icmp_types="echoreq"

comp3="192.168.0.3"

# options

set block-policy return
set loginterface egress
set skip on lo

# FTP Proxy rules

anchor "ftp-proxy/*"

pass in quick on $int_if inet proto tcp to any port ftp \
    divert-to 127.0.0.1 port 8021

# match rules

match out on egress inet from !(egress:network) to any nat-to (egress:0)

# filter rules

block in log
pass out quick

antispoof quick for { lo $int_if }

pass in on egress inet proto tcp from any to (egress) \
    port $tcp_services

pass in on egress inet proto tcp to (egress) port 80 rdr-to $comp3

pass in inet proto icmp all icmp-type $icmp_types

pass in on $int_if
```

## PHP

```php
require_once 'Zend/Uri/Http.php';

namespace Location\Web;

interface Factory
{
    static function _factory();
}

abstract class URI extends BaseURI implements Factory
{
    abstract function test();

    public static $st1 = 1;
    const ME = "Yo";
    var $list = NULL;
    private $var;

    /**
     * Returns a URI
     *
     * @return URI
     */
    static public function _factory($stats = array(), $uri = 'http')
    {
        echo __METHOD__;
        $uri = explode(':', $uri, 0b10);
        $schemeSpecific = isset($uri[1]) ? $uri[1] : '';
        $desc = 'Multi
line description';

        // Security check
        if (!ctype_alnum($scheme)) {
            throw new Zend_Uri_Exception('Illegal scheme');
        }

        $this->var = 0 - self::$st;
        $this->list = list(Array("1"=> 2, 2=>self::ME, 3 => \Location\Web\URI::class));

        return [
            'uri'   => $uri,
            'value' => null,
        ];
    }
}

echo URI::ME . URI::$st1;

__halt_compiler () ; datahere
datahere
datahere */
datahere
```

## PowerShell

```powershell
$initialDate = [datetime]'2013/1/8'

$rollingDate = $initialDate

do {
    $client = New-Object System.Net.WebClient
    $results = $client.DownloadString("http://not.a.real.url")
    Write-Host "$rollingDate.ToShortDateString() - $results"
    $rollingDate = $rollingDate.AddDays(21)
    $username = [System.Environment]::UserName
} until ($rollingDate -ge [datetime]'2013/12/31')
```

## Processing

```processing
import java.util.LinkedList;
import java.awt.Point;

PGraphics pg;
String load;

void setup() {
  size(displayWidth, displayHeight, P3D);
  pg = createGraphics(displayWidth*2,displayHeight,P2D);
  pg.beginDraw();
  pg.background(255,255,255);
  //pg.smooth(8);
  pg.endDraw();
}
void draw(){
  background(255);
}
```

## Python profile

```python-profile
       261917242 function calls in 686.251 CPU seconds

       ncalls  tottime  filename:lineno(function)
       152824  513.894  {method 'sort' of 'list' objects}
    129590630   83.894  rrule.py:842(__cmp__)
    129590630   82.439  {cmp}
       153900    1.296  rrule.py:399(_iter)
304393/151570    0.963  rrule.py:102(_iter_cached)
```

## Prolog

```prolog
mergesort([],[]). % special case
mergesort([A],[A]).
mergesort([A,B|R],S) :-
   split([A,B|R],L1,L2),
   mergesort(L1,S1),
   mergesort(L2,S2),
   merge(S1,S2,S).

split([],[],[]).
split([A],[A],[]).
split([A,B|R],[A|Ra],[B|Rb]) :-  split(R,Ra,Rb).
```

## Protocol Buffers

```protocol-buffers
package languages.protobuf;

option java_package = "org.highlightjs.languages.protobuf";

message Customer {
  required int64 customer_id = 1;
  optional string name = 2;
  optional string real_name = 3 [default = "Anonymous"];
  optional Gender gender = 4;
  repeated string email_addresses = 5;

  optional bool is_admin = 6 [default = false]; // or should this be a repeated field in Account?

  enum Gender {
    MALE = 1,
    FEMALE = 2
  }
}

service CustomerSearch {
  rpc FirstMatch(CustomerRequest) returns (CustomerResponse);
  rpc AllMatches(CustomerRequest) returns (CustomerResponse);
}
```

## Puppet

```puppet
# EC2 sample

class ec2utils {

    # This must include the path to the Amazon EC2 tools
    $ec2path = ["/usr/bin", "/bin", "/usr/sbin", "/sbin",
                "/opt/ec2/ec2-api-tools/bin",
                "/opt/ec2/aws-elb-tools/bin"]

    define elasticip ($instanceid, $ip)
    {
        exec { "ec2-associate-address-$name":
            logoutput   => on_failure,
            environment => $ec2utils::ec2env,
            path        => $ec2utils::ec2path,
            command     => "ec2assocaddr $ip \
                                         -i $instanceid",
            # Only do this when necessary
            unless => "test `ec2daddr $ip | awk '{print \$3}'` == $instanceid",
        }
    }

    mount { "$mountpoint":
        device  => $devicetomount,
        ensure  => mounted,
        fstype  => $fstype,
        options => $mountoptions,
        require => [ Exec["ec2-attach-volume-$name"],
                     File["$mountpoint"]
        ],
    }

}
```

## Python

```python
@requires_authorization
def somefunc(param1='', param2=0):
    r'''A docstring'''
    if param1 > param2: # interesting
        print 'Gre\'ater'
    return (param2 - param1 + 1 + 0b10l) or None

class SomeClass:
    pass

>>> message = '''interpreter
... prompt'''
```

## Q

```q
select time, price by date,stock from quote where price=(max;price)fby stock
data:raze value flip trade
select vwap:size wavg price by 5 xbar time.minute from aapl where date within (.z.d-10;.z.d)
f1:{[x;y;z] show (x;y+z);sum 1 2 3}
.z.pc:{[handle] show -3!(`long$.z.p;"Closed";handle)}
// random normal distribution, e.g. nor 10
nor:{$[x=2*n:x div 2;raze sqrt[-2*log n?1f]*/:(sin;cos)@\:(2*pi)*n?1f;-1_.z.s 1+x]}

mode:{where g=max g:count each group x}		// mode function
```

## R

```r
library(ggplot2)

centre <- function(x, type, ...) {
  switch(type,
         mean = mean(x),
         median = median(x),
         trimmed = mean(x, trim = .1))
}

myVar1
myVar.2
data$x
foo "bar" baz
# test "test"
"test # test"

(123) (1) (10) (0.1) (.2) (1e-7)
(1.2e+7) (2e) (3e+10) (0x0) (0xa)
(0xabcdef1234567890) (123L) (1L)
(0x10L) (10000000L) (1e6L) (1.1L)
(1e-3L) (4123.381E-10i)
(3.) (3.E10) # BUG: .E10 should be part of number

# Numbers in some different contexts
1L
0x40
.234
3.
1L + 30
plot(cars, xlim=20)
plot(cars, xlim=0x20)
foo<-30
my.data.3 <- read() # not a number
c(1,2,3)
1%%2

"this is a quote that spans
multiple lines
\"

is this still a quote? it should be.
# even still!

" # now we're done.

'same for
single quotes #'

# keywords
NULL, NA, TRUE, FALSE, Inf, NaN, NA_integer_,
NA_real_, NA_character_, NA_complex_, function,
while, repeat, for, if, in, else, next, break,
..., ..1, ..2

# not keywords
the quick brown fox jumped over the lazy dogs
null na true false inf nan na_integer_ na_real_
na_character_ na_complex_ Function While Repeat
For If In Else Next Break .. .... "NULL" `NULL` 'NULL'

# operators
+, -, *, /, %%, ^, >, >=, <, <=, ==, !=, !, &, |, ~,
->, <-, <<-, $, :, ::

# infix operator
foo %union% bar
%"test"%
`"test"`

```

## RenderMan RIB

```rib
FrameBegin 0
Display "Scene" "framebuffer" "rgb"
Option "searchpath" "shader" "+&:/home/kew"
Option "trace" "int maxdepth" [4]
Attribute "visibility" "trace" [1]
Attribute "irradiance" "maxerror" [0.1]
Attribute "visibility" "transmission" "opaque"
Format 640 480 1.0
ShadingRate 2
PixelFilter "catmull-rom" 1 1
PixelSamples 4 4
Projection "perspective" "fov" 49.5502811377
Scale 1 1 -1

WorldBegin

ReadArchive "Lamp.002_Light/instance.rib"
Surface "plastic"
ReadArchive "Cube.004_Mesh/instance.rib"
# ReadArchive "Sphere.010_Mesh/instance.rib"
# ReadArchive "Sphere.009_Mesh/instance.rib"
ReadArchive "Sphere.006_Mesh/instance.rib"

WorldEnd
FrameEnd
```

## Roboconf

```roboconf
# This is a comment
import toto.graph;

##
# Facet
##
facet VM {
	installer: iaas;
}

# Components
VM_ec2 {
	facets: VM;
	children: cluster-node, mysql;
}

VM_openstack {
	facets: VM;
	children: cluster-node, mysql;
}

cluster-node {
	alias: a cluster node;
	installer: puppet;
	exports: ip, port, optional-property1, optional_property2;
	imports: cluster-node.ip (optional), cluster-node.port (optional), mysql.ip, mysql.port;
}

mysql {
	alias: a MySQL database;
	installer: puppet;
	exports: ip, port;
}

##
# Normally, instances are defined in another file...
##
instance of VM_ec2 {
	name: VM_;
	count: 3;
	my-instance-property: whatever;
	
	instance of cluster-node {
		name: cluster node;		# An in-line comment
	}
}

instance of VM_openstack {
	name: VM_database;
	
	instance of mysql {
		name: mysql;
	}
}
```

## RenderMan RSL

```rsl
#define TEST_DEFINE 3.14
/*  plastic surface shader
 *
 *  Pixie is:
 *  (c) Copyright 1999-2003 Okan Arikan. All rights reserved.
 */

surface plastic (float Ka = 1, Kd = 0.5, Ks = 0.5, roughness = 0.1;
                 color specularcolor = 1;) {
  normal Nf = faceforward (normalize(N),I);
  Ci = Cs * (Ka*ambient() + Kd*diffuse(Nf)) + specularcolor * Ks *
       specular(Nf,-normalize(I),roughness);
  Oi = Os;
  Ci *= Oi;
}
```

## Ruby

```ruby
class A < B; def self.create(object = User) object end end
class Zebra; def inspect; "X#{2 + self.object_id}" end end

module ABC::DEF
  include Comparable

  # @param test
  # @return [String] nothing
  def foo(test)
    Thread.new do |blockvar|
      ABC::DEF.reverse(:a_symbol, :'a symbol', :<=>, 'test' + ?\012)
      answer = valid?4 && valid?CONST && ?A && ?A.ord
    end.join
  end

  def [](index) self[index] end
  def ==(other) other == self end
end

class Car < ActiveRecord::Base
  has_many :wheels, class_name: 'Wheel', foreign_key: 'car_id'
  scope :available, -> { where(available: true) }
end

hash = {1 => 'one', 2 => 'two'}

2.0.0p0 :001 > ['some']
 => ["some"]
```

## Oracle Rules Language

```ruleslanguage
//This is a comment
ABORT "You experienced an abort.";
WARN "THIS IS A WARNING";
CALL "RIDER_X";
DONE;
FOR EACH X IN CSV_FILE "d:\lodestar\user\d377.lse"
 LEAVE FOR;
END FOR;
IF ((BILL_KW = 0) AND (KW > 0)) THEN
END IF;
INCLUDE "R1";
LEAVE RIDER;
SELECT BILL_PERIOD
   WHEN "WINTER"
      BLOCK KWH
      FROM 0 TO 400 CHARGE $0.03709
      FROM 400 CHARGE $0.03000
      TOTAL $ENERGY_CHARGE_WIN;
   WHEN "SUMMER"
      $VOLTAGE_DISCOUNT_SUM = $0.00
   OTHERWISE
      $VOLTAGE_DISCOUNT_SUM = $1.00
END SELECT;
/* Report top five peaks */
LABEL PK.NM "Peak Number";
SAVE_UPDATE MV TO TABLE "METERVALUE";

FOR EACH INX IN ARRAYUPPERBOUND(#MYARRAY[])
  #MYARRAY[INX].VALUE = 2;
  CLEAR #MYARRAY[];
END FOR

//Interval Data
HNDL_1_ADD_EDI = INTDADDATTRIBUTE(HNDL_1, "EDI_TRANSACTION", EDI_ID);
HNDL_1_ADD_VAL_MSG = INTDADDVMSG(HNDL_1,"Missing (Status Code 9) values found");
EMPTY_HNDL = INTDCREATEHANDLE('05/03/2006 00:00:00', '05/03/2006 23:59:59', 3600, "Y", "0", " ");
```

## Rust

```rust
use std;

#![warn(unstable)]

/* Factorial */
fn fac(n: int) -> int {
    let s: str = "This is
a multi-line string.

It ends with an unescaped '\"'.";
    let c: char = 'Ф';
    let r: str = r##" raw string "##;

    let result = 1, i = 1;
    while i <= n { // No parens around the condition
        result *= i;
        i += 1;
    }
    ret result;
}

pure fn pure_length<T>(ls: list<T>) -> uint { /* ... */ }

type t = map::hashtbl<int,str>;
let x = id::<int>(10);

// Define some modules.
#[path = "foo.rs"]
mod foo;

impl <T> Seq<T> for [T] {
    fn len() -> uint { vec::len(self) }
    fn iter(b: fn(T)) {
        for elt in self { b(elt); }
    }
}

enum list<T> {
    Nil;
    Cons(T, @list<T>);
}

let a: list<int> = Cons(7, @cons(13, @nil));

struct Baz<'a> {
    baz: &'a str,
}

'h: for i in range(0,10) {
    'g: loop {
        if i % 2 == 0 { continue 'h; }
        if i == 9 { break 'h; }
        break 'g;
    }
}
```

## Scala

```scala
/**
 * A person has a name and an age.
 */
case class Person(name: String, age: Int)

// beware Int.MinValue
def absoluteValue(n: Int): Int =
  if (n < 0) -n else n

def interp(n: Int): String =
  s"there are $n ${color} balloons.\n"

type ξ[A] = (A, A)

trait Hist { lhs =>
  def ⊕(rhs: Hist): Hist
}

def gsum[A: Ring](as: Seq[A]): A =
  as.foldLeft(Ring[A].zero)(_ + _)

val actions: List[Symbol] =
  'init :: 'read :: 'write :: 'close :: Nil

trait Cake {
  type T;
  type Q
  val things: Seq[T]

  abstract class Spindler

  def spindle(s: Spindler, ts: Seq[T], reversed: Boolean = false): Seq[Q]
}

val colors = Map(
  "red"       -> 0xFF0000,
  "turquoise" -> 0x00FFFF,
  "black"     -> 0x000000,
  "orange"    -> 0xFF8040,
  "brown"     -> 0x804000)

lazy val ns = for {
  x <- 0 until 100
  y <- 0 until 100
} yield (x + y) * 33.33
```

## Scheme

```scheme
;; Calculation of Hofstadter's male and female sequences as a list of pairs

(define (hofstadter-male-female n)
(letrec ((female (lambda (n)
           (if (= n 0)
           1
           (- n (male (female (- n 1)))))))
     (male (lambda (n)
         (if (= n 0)
             0
             (- n (female (male (- n 1))))))))
  (let loop ((i 0))
    (if (> i n)
    '()
    (cons (cons (female i)
            (male i))
      (loop (+ i 1)))))))

(hofstadter-male-female 8)

(define (find-first func lst)
(call-with-current-continuation
 (lambda (return-immediately)
   (for-each (lambda (x)
       (if (func x)
           (return-immediately x)))
         lst)
   #f)))
```

## Scilab

```scilab
// A comment
function I = foo(dims, varargin)
  d=[1; matrix(dims(1:$-1),-1,1)]
  for i=1:size(varargin)
    if varargin(i)==[] then
       I=[],
       return;
    end
  end
endfunction

b = cos(a) + cosh(a);
bar_matrix = [ "Hello", "world" ];
foo_matrix = [1, 2, 3; 4, 5, 6];
```

## SCSS

```scss
@import "compass/reset";

// variables
$colorGreen: #008000;
$colorGreenDark: darken($colorGreen, 10);

@mixin container {
    max-width: 980px;
}

// mixins with parameters
@mixin button($color:green) {
    @if ($color == green) {
        background-color: #008000;
    }
    @else if ($color == red) {
        background-color: #B22222;
    }
}

button {
    @include button(red);
}

div,
.navbar,
#header,
input[type="input"] {
    font-family: "Helvetica Neue", Arial, sans-serif;
    width: auto;
    margin: 0 auto;
    display: block;
}

.row-12 > [class*="spans"] {
    border-left: 1px solid #B5C583;
}

// nested definitions
ul {
    width: 100%;
    padding: {
        left: 5px; right: 5px;
    }
  li {
      float: left; margin-right: 10px;
      .home {
          background: url('http://placehold.it/20') scroll no-repeat 0 0;
    }
  }
}

.banner {
    @extend .container;
}

a {
  color: $colorGreen;
  &:hover { color: $colorGreenDark; }
  &:visited { color: #c458cb; }
}

@for $i from 1 through 5 {
    .span#{$i} {
        width: 20px*$i;
    }
}

@mixin mobile {
  @media screen and (max-width : 600px) {
    @content;
  }
}
```

## Smali

```smali
.class public Lcom/test/Preferences;
.super Landroid/preference/PreferenceActivity;
.source "Preferences.java"


# instance fields
.field private PACKAGE_NAME:Ljava/lang/String;


# direct methods
.method public constructor <init>()V
    .registers 1
    .annotation build Landroid/annotation/SuppressLint;
        value = {
            "InlinedApi"
        }
    .end annotation

    .prologue
    .line 25
    invoke-direct {p0}, Landroid/preference/PreferenceActivity;-><init>()V

    const-string v4, "ASDF!"

    .line 156
    .end local v0           #customOther:Landroid/preference/Preference;
    .end local v1           #customRate:Landroid/preference/Preference;
    .end local v2           #hideApp:Landroid/preference/Preference;
    :cond_56

        .line 135
    invoke-static {p1}, Lcom/google/ads/AdActivity;->b(Lcom/google/ads/internal/d;)Lcom/google/ads/internal/d;

    .line 140
    :cond_e
    monitor-exit v1
    :try_end_f
    .catchall {:try_start_5 .. :try_end_f} :catchall_30

    .line 143
    invoke-virtual {p1}, Lcom/google/ads/internal/d;->g()Lcom/google/ads/m;

    move-result-object v0

    iget-object v0, v0, Lcom/google/ads/m;->c:Lcom/google/ads/util/i$d;

    invoke-virtual {v0}, Lcom/google/ads/util/i$d;->a()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/app/Activity;

    .line 144
    if-nez v0, :cond_33

    .line 145
    const-string v0, "activity was null while launching an AdActivity."

    invoke-static {v0}, Lcom/google/ads/util/b;->e(Ljava/lang/String;)V

    .line 160
    :goto_22
    return-void

    .line 136
    :cond_23
    :try_start_23
    invoke-static {}, Lcom/google/ads/AdActivity;->c()Lcom/google/ads/internal/d;

    move-result-object v0

    if-eq v0, p1, :cond_e

    return-void
.end method
```

## Smalltalk

```smalltalk
Object>>method: num
    "comment 123"
    | var1 var2 |
    (1 to: num) do: [:i | |var| ^i].
    Klass with: var1.
    Klass new.
    arr := #('123' 123.345 #hello Transcript var $@).
    arr := #().
    var2 = arr at: 3.
    ^ self abc

heapExample
    "HeapTest new heapExample"
    "Multiline
    decription"
    | n rnd array time sorted |
    n := 5000.
    "# of elements to sort"
    rnd := Random new.
    array := (1 to: n)
                collect: [:i | rnd next].
    "First, the heap version"
    time := Time
                millisecondsToRun: [sorted := Heap withAll: array.
    1
        to: n
        do: [:i |
            sorted removeFirst.
            sorted add: rnd next]].
    Transcript cr; show: 'Time for Heap: ' , time printString , ' msecs'.
    "The quicksort version"
    time := Time
                millisecondsToRun: [sorted := SortedCollection withAll: array.
    1
        to: n
        do: [:i |
            sorted removeFirst.
            sorted add: rnd next]].
    Transcript cr; show: 'Time for SortedCollection: ' , time printString , ' msecs'
```

## SML

```sml
(* list.sml
 *
 * COPYRIGHT (c) 2009 The Fellowship of SML/NJ (http://www.smlnj.org)
 * All rights reserved.
 *
 * Available (unqualified) at top level:
 *   type list
 *   val nil, ::, hd, tl, null, length, @, app, map, foldr, foldl, rev
 *   exception Empty
 *
 * Consequently the following are not visible at top level:
 *   val last, nth, take, drop, concat, revAppend, mapPartial, find, filter,
 *       partition, exists, all, tabulate
 *
 * The following infix declarations will hold at top level:
 *   infixr 5 :: @
 *
 *)

structure List : LIST =
  struct

    val op +  = InlineT.DfltInt.+
    val op -  = InlineT.DfltInt.-
    val op <  = InlineT.DfltInt.<
    val op <= = InlineT.DfltInt.<=
    val op >  = InlineT.DfltInt.>
    val op >= = InlineT.DfltInt.>=
(*    val op =  = InlineT.= *)

    datatype list = datatype list

    exception Empty = Empty

  (* these functions are implemented in base/system/smlnj/init/pervasive.sml *)
    val null = null
    val hd = hd
    val tl = tl
    val length = length
    val rev = rev
    val revAppend = revAppend
    val op @ = op @
    val foldr = foldr
    val foldl = foldl
    val app = app
    val map = map

    fun last [] = raise Empty
      | last [x] = x
      | last (_::r) = last r

    fun getItem [] = NONE
      | getItem (x::r) = SOME(x, r)

    fun nth (l,n) = let
          fun loop ((e::_),0) = e
            | loop ([],_) = raise Subscript
            | loop ((_::t),n) = loop(t,n-1)
          in
            if n >= 0 then loop (l,n) else raise Subscript
          end

    fun take (l, n) = let
          fun loop (l, 0) = []
            | loop ([], _) = raise Subscript
            | loop ((x::t), n) = x :: loop (t, n-1)
          in
            if n >= 0 then loop (l, n) else raise Subscript
          end

    fun drop (l, n) = let
          fun loop (l,0) = l
            | loop ([],_) = raise Subscript
            | loop ((_::t),n) = loop(t,n-1)
          in
            if n >= 0 then loop (l,n) else raise Subscript
          end


    fun concat [] = []
      | concat (l::r) = l @ concat r

    fun mapPartial pred l = let
          fun mapp ([], l) = rev l
            | mapp (x::r, l) = (case (pred x)
                 of SOME y => mapp(r, y::l)
                  | NONE => mapp(r, l)
                (* end case *))
          in
            mapp (l, [])
          end

    fun find pred [] = NONE
      | find pred (a::rest) = if pred a then SOME a else (find pred rest)

    fun filter pred [] = []
      | filter pred (a::rest) = if pred a then a::(filter pred rest) 
                                else (filter pred rest)

    fun partition pred l = let
          fun loop ([],trueList,falseList) = (rev trueList, rev falseList)
            | loop (h::t,trueList,falseList) = 
                if pred h then loop(t, h::trueList, falseList)
                else loop(t, trueList, h::falseList)
          in loop (l,[],[]) end


    fun exists pred = let 
          fun f [] = false
            | f (h::t) = pred h orelse f t
          in f end
    fun all pred = let 
          fun f [] = true
            | f (h::t) = pred h andalso f t
          in f end

    fun tabulate (len, genfn) = 
          if len < 0 then raise Size
          else let
            fun loop n = if n = len then []
                         else (genfn n)::(loop(n+1))
            in loop 0 end

    fun collate compare = let
  fun loop ([], []) = EQUAL
    | loop ([], _) = LESS
    | loop (_, []) = GREATER
    | loop (x :: xs, y :: ys) =
      (case compare (x, y) of
     EQUAL => loop (xs, ys)
         | unequal => unequal)
    in
  loop
    end

  end (* structure List *)

```

## SQF

```sqf
/***
	Arma Scripting File
	Edition: 0.13
***/

// Enable eating to improve health.
_unit addAction ["Eat Energy Bar", {
    if (_this getVariable ["EB_NumActivation", 0] > 0) then {
        _this setDamage (0 max (damage _this - 0.25));
    } else {
        hint "You have eaten it all";
    };
    // 4 - means something...
    ["EB_Eaten", _this, 4] call events_notify;
}];
```

## SQL

```sql
BEGIN;
CREATE TABLE "topic" (
    -- This is the greatest table of all time
    "id" serial NOT NULL PRIMARY KEY,
    "forum_id" integer NOT NULL,
    "subject" varchar(255) NOT NULL -- Because nobody likes an empty subject
);
ALTER TABLE "topic" ADD CONSTRAINT forum_id FOREIGN KEY ("forum_id") REFERENCES "forum" ("id");

-- Initials
insert into "topic" ("forum_id", "subject") values (2, 'D''artagnian');

select /* comment */ count(*) from cicero_forum;

-- this line lacks ; at the end to allow people to be sloppy and omit it in one-liners
/*
but who cares?
*/
COMMIT
```

## Stata

```stata
program define gr_log
version 6.0

local or = `2'
local xunits = `3'
local b1 = ln(`or')

* make summary of logistic data from equation
set obs `xunits'
generate pgty = 1 - 1/(1 + exp(score))
/**
 * Comment 1
*/
reg y x
* Comment 2
reg y2 x //comment 3
This is a `loc' $glob ${glob2}
This is a `"string " "' "string`1'two${hi}" bad `"string " "' good `"string " "'

//Limit to just the project ados
cap adopath - SITE
cap adopath - PLUS
/*cap adopath - PERSONAL
cap adopath - OLDPLACE*/
adopath ++ "${dir_base}/code/ado/"
A string `"Wow"'. `""one" "two""'
A `local' em`b'ed
a global ${dir_base} $dir_base em${b}ed

forval i=1/4{
  if `i'==2{
    cap reg y x1, robust
    local x = ln(4)
    local x =ln(4)
    local ln = ln
  }
}
 
* add mlibs in the new adopath to the index
mata: mata mlib index
```

## STEP Part 21 (ISO 10303-21)

```step21
ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('CUBE_4SQUARE','2013-11-29T',('acook'),(''),
'SOMETHINGCAD BY SOME CORPORATION, 2012130',
'SOMETHINGCAD BY SOME CORPORATION, 2012130','');
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;
/* file written by SomethingCAD */
DATA;
#1=DIRECTION('',(1.E0,0.E0,0.E0));
#2=VECTOR('',#1,4.E0);
#3=CARTESIAN_POINT('',(-2.E0,-2.E0,-2.E0));
#4=LINE('',#3,#2);
#5=DIRECTION('',(0.E0,1.E0,0.E0));
#6=VECTOR('',#5,4.E0);
#7=CARTESIAN_POINT('',(2.E0,-2.E0,-2.E0));
#8=LINE('',#7,#6);
#9=DIRECTION('',(-1.E0,0.E0,0.E0));
#10=VECTOR('',#9,4.E0);
#11=CARTESIAN_POINT('',(2.E0,2.E0,-2.E0));
#12=LINE('',#11,#10);
#13=DIRECTION('',(0.E0,-1.E0,0.E0));
#14=VECTOR('',#13,4.E0);
#15=CARTESIAN_POINT('',(-2.E0,2.E0,-2.E0));
#16=LINE('',#15,#14);
#17=DIRECTION('',(0.E0,0.E0,1.E0));
#18=VECTOR('',#17,4.E0);
#19=CARTESIAN_POINT('',(-2.E0,-2.E0,-2.E0));
#20=LINE('',#19,#18);
#21=DIRECTION('',(0.E0,0.E0,1.E0));
ENDSEC;
END-ISO-10303-21;
```

## Stylus

```stylus
@import "nib"

// variables
$green = #008000
$green_dark = darken($green, 10)

// mixin/function
container()
  max-width 980px

// mixin/function with parameters
buttonBG($color = green)
  if $color == green
    background-color #008000
  else if $color == red
    background-color #B22222

button
  buttonBG(red)

#content, .content
  font Tahoma, Chunkfive, sans-serif
  background url('hatch.png')
  color #F0F0F0 !important
  width 100%
```

## Swift

```swift
extension MyClass : Interface {
    class func unarchiveFromFile<A>(file : A, (Int,Int) -> B) -> SKNode? {
        let path: String = bundle.pathForResource(file, ofType: "file\(name + 5).txt")
        let funnyNumber = 3 + 0xC2.15p2 * (1_000_000.000_000_1 - 000123.456) + 0o21
        var sceneData = NSData.dataWithContentsOfFile(path, options: .DataReadingMappedIfSafe, error: nil)
        /* a comment /* with a nested comment */ and the end */
    }
    @objc override func shouldAutorotate() {
        return true
    }
}
```

## Tcl

```tcl
package json

source helper.tcl
# randomness verified by a die throw
set ::rand 4

proc give::recursive::count {base p} { ; # 2 mandatory params
    while {$p > 0} {
        set result [expr $result * $base]; incr p -1
    }
    return $result
}

set a 'a'; set b "bcdef"; set lst [list "item"]
puts [llength $a$b]

set ::my::tid($id) $::my::tid(def)
lappend lst $arr($idx) $::my::arr($idx) $ar(key)
lreplace ::my::tid($id) 4 4
puts $::rand ${::rand} ${::AWESOME::component::variable}

puts "$x + $y is\t [expr $x + $y]"

proc isprime x {
    expr {$x>1 && ![regexp {^(oo+?)\1+$} [string repeat o $x]]}
}
```

## TeX

```tex
\documentclass{article}
\usepackage[koi8-r]{inputenc}
\hoffset=0pt
\voffset=.3em
\tolerance=400
\newcommand{\eTiX}{\TeX}
\begin{document}
\section*{Highlight.js}
\begin{table}[c|c]
$\frac 12\, + \, \frac 1{x^3}\text{Hello \! world}$ & \textbf{Goodbye\~ world} \\\eTiX $ \pi=400 $
\end{table}
Ch\'erie, \c{c}a ne me pla\^\i t pas! % comment \b
G\"otterd\"ammerung~45\%=34.
$$
    \int\limits_{0}^{\pi}\frac{4}{x-7}=3
$$
\end{document}
```

## Thrift

```thrift
namespace * thrift.test

/**
 * Docstring!
 */
enum Numberz
{
  ONE = 1,
  TWO,
  THREE,
  FIVE = 5,
  SIX,
  EIGHT = 8
}

const Numberz myNumberz = Numberz.ONE;
// the following is expected to fail:
// const Numberz urNumberz = ONE;

typedef i64 UserId

struct Msg
{
  1: string message,
  2: i32 type
}
struct NestedListsI32x2
{
  1: list<list<i32>> integerlist
}
struct NestedListsI32x3
{
  1: list<list<list<i32>>> integerlist
}
service ThriftTest
{
  void        testVoid(),
  string      testString(1: string thing),
  oneway void testInit()
}
```

## TP

```tp
/PROG  ALL
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "";
PROG_SIZE	= 3689;
CREATE		= DATE 14-05-13  TIME 17:03:06;
MODIFIED	= DATE 14-05-13  TIME 17:21:44;
FILE_NAME	= ;
VERSION		= 0;
LINE_COUNT	= 118;
MEMORY_SIZE	= 4365;
PROTECT		= READ_WRITE;
TCD:  STACK_SIZE	= 0,
      TASK_PRIORITY	= 50,
      TIME_SLICE	= 0,
      BUSY_LAMP_OFF	= 0,
      ABORT_REQUEST	= 0,
      PAUSE_REQUEST	= 0;
DEFAULT_GROUP	= 1,*,*,*,*;
CONTROL_CODE	= 00000000 00000000;
/MN
  ! motion ;
J P[1:test point] 100% FINE    ;
J P[1] 100.0sec CNT100    ;
J P[1] 100msec CNT R[1]    ;
L P[1] 100/sec FINE    ;
L P[1] 100cm/min CNT100    ;
L P[1] 100.0inch/min CNT100    ;
L P[1] 100deg/sec CNT100    ;
  ! indirect speed ;
L P[1] R[1]sec CNT100    ;
  ! indirect indirect ;
L PR[1] R[R[1]]msec CNT100    ;
  ! indirect destination ;
L PR[R[1]] max_speed CNT100    ;
   ;
  ! assignment ;
  R[1]=R[2]    ;
  ! indirect assignment ;
  R[R[1]]=R[2] ;
  ! system variables ;
  $foo=$bar[100].$baz ;
  R[1]=$FOO.$BAR ;
    ;
  ! various keyword assignments ;
  PR[1]=LPOS    ;
  PR[1]=JPOS    ;
  PR[1]=UFRAME[1] ;
  PR[1]=UTOOL[1] ;
  PR[1]=P[1]    ;
  PR[1,1:component]=5    ;
  SR[1:string reg]=SR[2]+AR[1]    ;
  R[1]=SO[1:Cycle start] DIV SI[2:Remote]    ;
  R[1]=UO[1:Cmd enabled] MOD UI[1:*IMSTP]    ;
  ! mixed logic ;
  DO[1]=(DI[1] AND AR[1] AND F[1] OR TIMER[1]>TIMER_OVERFLOW[1]) ;
  F[1]=(ON) ;
  JOINT_MAX_SPEED[1]=5 ;
  LINEAR_MAX_SPEED=5 ;
  SKIP CONDITION DI[1]=OFF-   ;
  PAYLOAD[R[1]] ;
  OFFSET CONDITION PR[1]    ;
  UFRAME_NUM=1 ;
  UTOOL_NUM=1 ;
  UFRAME[1]=PR[1] ;
  UTOOL[1]=PR[1] ;
  RSR[1]=ENABLE ;
  RSR[AR[1]]=DISABLE ;
  UALM[1] ;
  TIMER[1]=START ;
  TIMER[1]=STOP ;
  TIMER[1]=RESET ;
  OVERRIDE=50% ;
  TOOL_OFFSET CONDITION PR[1]    ;
  LOCK PREG ;
  UNLOCK PREG ;
  COL DETECT ON ;
  COL DETECT OFF ;
  COL GUARD ADJUST R[1] ;
  COL GUARD ADJUST 50 ;
  MONITOR TEST ;
  MONITOR END TEST ;
  R[1]=STRLEN SR[1] ;
  SR[1]=SUBSTR SR[2],R[3],R[4] ;
  R[1]=FINDSTR SR[1],SR[2] ;
  DIAG_REC[1,5,2] ;
   ;
  ! program calls ;
  CALL TEST ;
  CALL TEST(1,'string',SR[1],AR[1]) ;
  RUN TEST ;
  RUN TEST(1,'string',SR[1],AR[1]) ;
   ;
  ! conditionals ;
  IF R[1]=1,JMP LBL[5] ;
  IF R[1]=AR[1],CALL TEST ;
  IF (DI[1]),R[1]=(5) ;
  SELECT R[1]=1,JMP LBL[5] ;
         =2,CALL TEST ;
         ELSE,JMP LBL[100] ;
  FOR R[1]=1 TO R[2] ;
  ENDFOR ;
   ;
  ! wait statement ;
  WAIT   1.00(sec) ;
  WAIT R[5] ;
  WAIT DI[1]=ON    ;
  WAIT DI[1]=ON+    ;
  WAIT ERR_NUM=1    ;
  WAIT (DI[1]=ON) ;
   ;
  ! jumps and labels ;
  JMP LBL[1] ;
  JMP LBL[R[1]] ;
  LBL[100] ;
  LBL[100:TEST] ;
   ;
  ! statements ;
  PAUSE ;
  ABORT ;
  ERROR_PROG=ALL ;
  RESUME_PROG[1]=TEST ;
  END ;
  MESSAGE[ASDF] ;
   ;
  ! comments ;
  --eg:ASDFASDFASDF ;
  // L P[9] 100mm/sec CNT100 ACC100    ;
   ;
  ! motion modifiers ;
L P[1] 100mm/sec CNT100 ACC100    ;
L P[1] 100mm/sec CNT100 ACC R[1]    ;
L P[1] 100mm/sec CNT100 Skip,LBL[1]    ;
L P[1] 100mm/sec CNT100 BREAK    ;
L P[1] 100mm/sec CNT100 Offset    ;
L P[1] 100mm/sec CNT100 PSPD50    ;
L P[1] 100mm/sec CNT100 Offset,PR[1]    ;
L P[1] 100mm/sec CNT100 INC    ;
L P[1] 100mm/sec CNT100 RT_LDR[1]    ;
L P[1] 100mm/sec CNT100 AP_LD50    ;
L P[1] 100mm/sec CNT100 Tool_Offset    ;
L P[1] 100mm/sec CNT100 Tool_Offset,PR[1]    ;
L P[1] 100mm/sec CNT100 Skip,LBL[1],PR[1]=LPOS    ;
L P[1] 100mm/sec CNT100 TB R[5]sec,CALL ALL    ;
L P[1] 100mm/sec CNT100 TA   0.00sec,AO[1]=R[5]    ;
L P[1] 100mm/sec CNT100 DB    0.0mm,CALL ALL    ;
L P[1] 100mm/sec CNT100 PTH    ;
L P[1] 100mm/sec CNT100 VOFFSET,VR[1] ;
/POS
P[1:"test"]{
   GP1:
	UF : 0, UT : 1,		CONFIG : '',
	X =   550.000  mm,	Y =     0.000  mm,	Z =  -685.000  mm,
	W =   180.000 deg,	P =     0.000 deg,	R =     0.000 deg
};
/END
```

## Twig

```twig
{% if posts|length %}
  {% for article in articles %}
  &lt;div&gt;
  {{ article.title|upper() }}

  {# outputs 'WELCOME' #}
  &lt;/div&gt;
  {% endfor %}
{% endif %}

{% set user = json_encode(user) %}

{{ random(['apple', 'orange', 'citrus']) }}

{{ include(template_from_string("Hello {{ name }}")) }}


{#
Comments may be long and multiline.
Markup is &lt;em&gt;not&lt;/em&gt; highlighted within comments.
#}
```

## TypeScript

```typescript
class MyClass {
    public static myValue: string;
    constructor(init: string) {
      this.myValue = init;
    }
  }
  import fs = require("fs");
  module MyModule {
    export interface MyInterface extends OtherInterface {
      myProperty: any;
    }
  }
  declare magicNumber number;
  myArray.forEach(() => {
    // fat arrow syntax
  });
```

## Vala

```vala
using DBus;

namespace Test {
  class Foo : Object {
    public signal void some_event ();   // definition of the signal
    public void method () {
      some_event ();                    // emitting the signal (callbacks get invoked)
    }
  }
}

/* defining a class */
class Track : GLib.Object, Test.Foo {              /* subclassing 'GLib.Object' */
  public double mass;                  /* a public field */
  public double name { get; set; }     /* a public property */
  private bool terminated = false;     /* a private field */
  public void terminate() {            /* a public method */
    terminated = true;
  }
}

const ALL_UPPER_CASE = "you should follow this convention";

var t = new Track();      // same as: Track t = new Track();
var s = "hello";          // same as: string s = "hello";
var l = new List<int>();       // same as: List<int> l = new List<int>();
var i = 10;               // same as: int i = 10;


#if (ololo)
Regex regex = /foo/;
#endif

/*
 * Entry point can be outside class
 */
void main () {
  var long_string = """
    Example of "verbatim string".
    Same as in @"string" in C#
  """
  var foo = new Foo ();
  foo.some_event.connect (callback_a);      // connecting the callback functions
  foo.some_event.connect (callback_b);
  foo.method ();
}
```

## VB.NET

```vb.net
Import System
Import System.IO
#Const DEBUG = True

Namespace Highlighter.Test
  ''' <summary>This is an example class.</summary>
  Public Class Program
    Protected Shared hello As Integer = 3
    Private Const ABC As Boolean = False

#Region "Code"
    ' Cheers!
    <STAThread()> _
    Public Shared Sub Main(ByVal args() As String, ParamArray arr As Object) Handles Form1.Click
      On Error Resume Next
      If ABC Then
        While ABC : Console.WriteLine() : End While
        For i As Long = 0 To 1000 Step 123
          Try
            System.Windows.Forms.MessageBox.Show(CInt("1").ToString())
          Catch ex As Exception       ' What are you doing? Well...
            Dim exp = CType(ex, IOException)
            REM ORZ
            Return
          End Try
        Next
      Else
        Dim l As New System.Collections.List<String>()
        SyncLock l
          If TypeOf l Is Decimal And l IsNot Nothing Then
            RemoveHandler button1.Paint, delegate
          End If
          Dim d = New System.Threading.Thread(AddressOf ThreadProc)
          Dim a = New Action(Sub(x, y) x + y)
          Static u = From x As String In l Select x.Substring(2, 4) Where x.Length > 0
        End SyncLock
        Do : Laugh() : Loop Until hello = 4
      End If
    End Sub
#End Region
  End Class
End Namespace
```

## VBScript in HTML

```vbscript-html
<body>
<%
If i <  10 Then
  response.write("Good morning!")
End If
%>
</body>
```

## VBScript

```vbscript
' creating configuration storage and initializing with default values
Set cfg = CreateObject("Scripting.Dictionary")

' reading ini file
for i = 0 to ubound(ini_strings)
    s = trim(ini_strings(i))

    ' skipping empty strings and comments
    if mid(s, 1, 1) <> "#" and len(s) > 0 then
      ' obtaining key and value
      parts = split(s, "=", -1, 1)

      if ubound(parts)+1 = 2 then
        parts(0) = trim(parts(0))
        parts(1) = trim(parts(1))

        ' reading configuration and filenames
        select case lcase(parts(0))
          case "uncompressed""_postfix" cfg.item("uncompressed""_postfix") = parts(1)
          case "f"
                    options = split(parts(1), "|", -1, 1)
                    if ubound(options)+1 = 2 then
                      ' 0: filename,  1: options
                      ff.add trim(options(0)), trim(options(1))
                    end if
        end select
      end if
    end if
next
```

## Verilog

```verilog
`timescale 1ns / 1ps

/**
 * counter: a generic clearable up-counter
 */

module counter
    #(parameter WIDTH=64)
    (
        input clk,
        input ce,
        input arst_n,
        output reg [WIDTH-1:0] q
    );

    // some child
    clock_buffer #(WIDTH) buffer_inst (
      .clk(clk),
      .ce(ce),
      .reset(arst_n)
    );

    // Simple gated up-counter with async clear

    always @(posedge clk or negedge arst_n) begin
        if (arst_n == 1'b0) begin
            q <= {WIDTH {1'b0}};
            end
        else begin
            q <= q;
            if (ce == 1'b1) begin
                q <= q + 1;
            end
        end
    end

endmodule
```

## VHDL

```vhdl
/*
 * RS-trigger with assynch. reset
 */

library ieee;
use ieee.std_logic_1164.all;

entity RS_trigger is
    generic (T: Time := 0ns);
    port ( R, S  : in  std_logic;
           Q, nQ : out std_logic;
           reset, clock : in  std_logic );
end RS_trigger;

architecture behaviour of RS_trigger is
    signal QT: std_logic; -- Q(t)
begin
    process(clock, reset) is
        subtype RS is std_logic_vector (1 downto 0);
    begin
        if reset = '0' then
            QT <= '0';
        else
            if rising_edge(C) then
                if not (R'stable(T) and S'stable(T)) then
                    QT <= 'X';
                else
                    case RS'(R&S) is
                        when "01" => QT <= '1';
                        when "10" => QT <= '0';
                        when "11" => QT <= 'X';
                        when others => null;
                    end case;
                end if;
            end if;
        end if;
    end process;

    Q  <= QT;
    nQ <= not QT;
end architecture behaviour;
```

## Vim Script

```vim-script
if foo > 2 || has("gui_running")
  syntax on
  set hlsearch
endif

set autoindent

" switch on highlighting
function UnComment(fl, ll)
  while idx >= a:ll
    let srclines=getline(idx)
    let dstlines=substitute(srclines, b:comment, "", "")
    call setline(idx, dstlines)
  endwhile
endfunction
```

## Intel x86 Assembly

```x86asm
section .text
extern  _MessageBoxA@16
%if     __NASM_VERSION_ID__ >= 0x02030000
safeseh handler         ; register handler as "safe handler"
%endif

handler:
        push    dword 1 ; MB_OKCANCEL
        push    dword caption
        push    dword text
        push    dword 0
        call    _MessageBoxA@16
        sub     eax,1   ; incidentally suits as return value
                        ; for exception handler
        ret

global  _main
_main:  push    dword handler
        push    dword [fs:0]
        mov     dword [fs:0], esp
        xor     eax,eax
        mov     eax, dword[eax]   ; cause exception
        pop     dword [fs:0]      ; disengage exception handler
        add     esp, 4
        ret

avx2:   vzeroupper
        push      rbx
        mov       rbx,   rsp
        sub       rsp,   0h20
        vmovdqa   ymm0,  [rcx]
        vpaddb    ymm0,  [rdx]
        leave
        ret

text:   db      'OK to rethrow, CANCEL to generate core dump',0
caption:db      'SEGV',0

section .drectve info
        db      '/defaultlib:user32.lib /defaultlib:msvcrt.lib '
```

## XL

```xl
import Animate
import SeasonsGreetingsTheme
import "myhelper.xl"
theme "SeasonsGreetings"
function X:real -> sin(X*0.5) + 16#0.002
page "A nice car",
// --------------------------------------
//    Display car model on a pedestal
// --------------------------------------
    clear_color 0, 0, 0, 1
    hand_scale -> 0.3

    // Display the background image
    background -4000,
        locally
            disable_depth_test
            corridor N:integer ->
                locally
                    rotatez 60 * N
                    translatex 1000
                    rotatey 90
                    color "white"
                    texture "stars.png"
                    texture_wrap true, true
                    texture_transform
                        translate (time + N) * 0.02 mod 1, 0, 0
                        scale 0.2, 0.3, 0.3
                    rectangle 0, 0, 100000, 1154
```

## HTML, XML

```markup
<?xml version="1.0"?>
<response value="ok" xml:lang="en">
  <text>Ok</text>
  <comment html_allowed="true"/>
  <ns1:description><![CDATA[
  CDATA is <not> magical.
  ]]></ns1:description>
  <a></a> <a/>
</response>


<!DOCTYPE html>
<title>Title</title>

<style>body {width: 500px;}</style>

<script type="application/javascript">
  function $init() {return true;}
</script>

<body>
  <p checked class="title" id='title'>Title</p>
  <!-- here goes the rest of the page -->
</body>
```

## XQuery

```xquery
declare option output:method 'json';

(
let $map := map { 'R': 'red', 'G': 'green', 'B': 'blue' }
return (
  $map?*          (: 1. returns all values; same as: map:keys($map) ! $map(.) :),
  $map?R          (: 2. returns the value associated with the key 'R'; same as: $map('R') :),
  $map?('G','B')  (: 3. returns the values associated with the key 'G' and 'B' :)
),

('A', 'B', 'C') => count(),

for $country in db:open('factbook')//country
where $country/@population > 100000000
let $name := $country/name[1]
for $city in $country//city[population > 1000000]
group by $name
return <country name='{ $name }'>{ $city/name }</country>

)
```

## YAML

```yaml
---
# comment
string_1: "Bar"
string_2: 'bar'
string_3: bar
inline_keys_ignored: sompath/name/file.jpg
keywords_in_yaml:
  - true
  - false
  - TRUE
  - FALSE
  - 21
  - 21.0
  - !!str 123
"quoted_key": &foobar
  bar: foo
  foo:
  "foo": bar

reference: *foobar

multiline_1: |
  Multiline
  String
multiline_2: >
  Multiline
  String
multiline_3: "
  Multiline string
  "

ansible_variables: "foo {{variable}}"

array_nested:
- a
- b: 1
  c: 2
- b
- comment
```

## Zephir

```zephir
function testBefore(<Test> a, var b = 5, int c = 10)
{
    a->method1();

    return b + c;
}

namespace Test;

use RuntimeException as RE;

/**
 * Example comment
 */
class Test extends CustomClass implements TestInterface
{
    const C1 = null;

    // Magic constant: http://php.net/manual/ru/language.constants.predefined.php
    const className = __CLASS__;

    public function method1()
    {
        int a = 1, b = 2;
        return a + b;
    }

    // See fn is allowed like shortcut
    public fn method2() -> <Test>
    {
        call_user_func(function() { echo "hello"; });


        [1, 2, 3, 4, 5]->walk(
            function(int! x) {
                return x * x;
            }
        );

        [1, 2, 3, 4, 5]->walk(
            function(_, int key) { echo key; }
        );

        array input = [1, 2, 3, 4, 5];

        input->walk(
            function(_, int key) { echo key; }
        );


        input->map(x => x * x);

        return this;
    }
}
```
