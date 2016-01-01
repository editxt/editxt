# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: avrasm.js
name = 'AVR Assembler'
file_patterns = ['*.avrasm']

flags = re.IGNORECASE | re.MULTILINE

built_in = """
    r0 r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 r13 r14 r15 r16 r17 r18
    r19 r20 r21 r22 r23 r24 r25 r26 r27 r28 r29 r30 r31 x xh xl y yh yl
    z zh zl ucsr1c udr1 ucsr1a ucsr1b ubrr1l ubrr1h ucsr0c ubrr0h tccr3c
    tccr3a tccr3b tcnt3h tcnt3l ocr3ah ocr3al ocr3bh ocr3bl ocr3ch
    ocr3cl icr3h icr3l etimsk etifr tccr1c ocr1ch ocr1cl twcr twdr twar
    twsr twbr osccal xmcra xmcrb eicra spmcsr spmcr portg ddrg ping
    portf ddrf sreg sph spl xdiv rampz eicrb eimsk gimsk gicr eifr gifr
    timsk tifr mcucr mcucsr tccr0 tcnt0 ocr0 assr tccr1a tccr1b tcnt1h
    tcnt1l ocr1ah ocr1al ocr1bh ocr1bl icr1h icr1l tccr2 tcnt2 ocr2 ocdr
    wdtcr sfior eearh eearl eedr eecr porta ddra pina portb ddrb pinb
    portc ddrc pinc portd ddrd pind spdr spsr spcr udr0 ucsr0a ucsr0b
    ubrr0l acsr admux adcsr adch adcl porte ddre pine pinf
    """.split()

keyword = """
    adc add adiw and andi asr bclr bld brbc brbs brcc brcs break breq
    brge brhc brhs brid brie brlo brlt brmi brne brpl brsh brtc brts
    brvc brvs bset bst call cbi cbr clc clh cli cln clr cls clt clv clz
    com cp cpc cpi cpse dec eicall eijmp elpm eor fmul fmuls fmulsu
    icall ijmp in inc jmp ld ldd ldi lds lpm lsl lsr mov movw mul muls
    mulsu neg nop or ori out pop push rcall ret reti rjmp rol ror sbc
    sbr sbrc sbrs sec seh sbi sbci sbic sbis sbiw sei sen ser ses set
    sev sez sleep spm st std sts sub subi swap tst wdr
    """.split()

meta = """
    .byte .cseg .db .def .device .dseg .dw .endmacro .equ .eseg .exit
    .include .list .listmac .macro .nolist .org .set
    """.split()

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

number0 = [RE(r"\b(?:0b[01]+)")]

number1 = [RE(r"\b(?:\$[a-zA-Z0-9]+|0o[0-7]+)")]

symbol = [RE(r"^[A-Za-z0-9_.$]+:")]

subst = [RE(r"@[0-9]+")]

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
    ('meta', meta),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('comment', RE(r";"), [RE(r"$")], comment),
    ('number', number),
    ('number', number0),
    ('number', number1),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"[^\\]'")]),
    ('symbol', symbol),
    ('meta', RE(r"#"), [RE(r"$")]),
    ('subst', subst),
]
