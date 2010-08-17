from AppKit import NSCommandKeyMask, NSAlternateKeyMask, NSControlKeyMask
from editxt.textcommand import TextCommand


def loadCommands():
	return [MyTextCommand()]


class MyTextCommand(TextCommand):

	def title(self):
		"""Return the name of this command (a unicode string)"""
		return u"My Text Command"
	
	def execute(self, textview, sender):
		"""Execute the command (put your code here)"""
		raise NotImplementedError()

	def is_enabled(self, textview, menuitem):
		return True

	def preferred_hotkey(self):
		"""Get the preferred hotkey for this text command
		
		Returns a tuple or None. If a tuple is returned it should contain two
		values: (<key string>, <modifier mask>). For more info see NSMenuItem
		setKeyEquivalent: and setKeyEquivalentModifierMask: in the Cocoa
		documentation.
		"""
		return None # no hotkey by default
