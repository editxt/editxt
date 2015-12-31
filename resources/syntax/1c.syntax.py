# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: 1c.js
name = '1C'
file_patterns = ['*.1c']

flags = re.IGNORECASE | re.MULTILINE

built_in = """
    ansitooem oemtoansi ввестивидсубконто ввестидату ввестизначение
    ввестиперечисление ввестипериод ввестиплансчетов ввестистроку
    ввестичисло вопрос восстановитьзначение врег выбранныйплансчетов
    вызватьисключение датагод датамесяц датачисло добавитьмесяц
    завершитьработусистемы заголовоксистемы записьжурналарегистрации
    запуститьприложение зафиксироватьтранзакцию значениевстроку
    значениевстрокувнутр значениевфайл значениеизстроки
    значениеизстрокивнутр значениеизфайла имякомпьютера имяпользователя
    каталогвременныхфайлов каталогиб каталогпользователя
    каталогпрограммы кодсимв командасистемы конгода конецпериодаби
    конецрассчитанногопериодаби конецстандартногоинтервала конквартала
    конмесяца коннедели лев лог лог10 макс
    максимальноеколичествосубконто мин монопольныйрежим
    названиеинтерфейса названиенабораправ назначитьвид назначитьсчет
    найти найтипомеченныенаудаление найтиссылки началопериодаби
    началостандартногоинтервала начатьтранзакцию начгода начквартала
    начмесяца начнедели номерднягода номерднянедели номернеделигода нрег
    обработкаожидания окр описаниеошибки основнойжурналрасчетов
    основнойплансчетов основнойязык открытьформу открытьформумодально
    отменитьтранзакцию очиститьокносообщений периодстр
    полноеимяпользователя получитьвремята получитьдатута
    получитьдокументта получитьзначенияотбора получитьпозициюта
    получитьпустоезначение получитьта прав праводоступа предупреждение
    префиксавтонумерации пустаястрока пустоезначение
    рабочаядаттьпустоезначение рабочаядата разделительстраниц
    разделительстрок разм разобратьпозициюдокумента рассчитатьрегистрына
    рассчитатьрегистрыпо сигнал симв символтабуляции создатьобъект сокрл
    сокрлп сокрп сообщить состояние сохранитьзначение сред
    статусвозврата стрдлина стрзаменить стрколичествострок
    стрполучитьстроку стрчисловхождений сформироватьпозициюдокумента
    счетпокоду текущаядата текущеевремя типзначения типзначениястр
    удалитьобъекты установитьтана установитьтапо фиксшаблон формат цел
    шаблон
    """.split()

keyword = """
    возврат дата для если и или иначе иначеесли исключение конецесли
    конецпопытки конецпроцедуры конецфункции конеццикла константа не
    перейти перем перечисление по пока попытка прервать продолжить
    процедура строка тогда фс функция цикл число экспорт
    """.split()

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

number = [RE(r"\b\d+(?:\.\d+)?")]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '""'},
    ]

keyword0 = ['процедура', 'функция']

keyword1 = ['экспорт']

class _group0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword1),
        None,  # rules[2],
    ]

keyword2 = ['знач']

class params:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword2),
        None,  # rules[4],
        None,  # rules[5],
    ]

title = [RE(r"[a-zA-Zа-яА-Я][a-zA-Z0-9_а-яА-Я]*")]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('_group0', RE(r"экспорт"), [RE(r"\B\b")], _group0),
        ('params', RE(r"\("), [RE(r"\)")], params),
        None,  # rules[2],
        ('title', title),
    ]

number0 = [RE(r"'\d{2}\.\d{2}\.(?:\d{2}|\d{4})'")]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('number', number),
    ('string', RE(r"\""), [RE(r"\"|$")], string),
    ('string', RE(r"\|"), [RE(r"\"|$")], string),
    ('function', RE(r"(?:процедура|функция)"), [RE(r"$")], function),
    ('meta', RE(r"#"), [RE(r"$")]),
    ('number', number0),
]

_group0.rules[1] = rules[2]
params.rules[1] = rules[4]
params.rules[2] = rules[5]
function.rules[3] = rules[2]
