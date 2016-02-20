GENERAL = 'general'
FIND = 'find'

_pasteboards = {}

class Pasteboard:

    def __new__(cls, name=GENERAL):
        try:
            obj = _pasteboards[name]
        except KeyError:
            obj = _pasteboards[name] = super().__new__(cls)
            obj.name = name
        return obj

    text = None
