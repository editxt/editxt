"""A sample text command

A text command is a callable object (most often a function) with a particular
set of attributes. The attributes are most conveniently applied with the
@command decorator, which supplies defaults and allows them to be overridden.

@command decorator parameters:
    names - One or more names that can be typed in the command bar to
    	invoke the command. This can be a space-delimited string or a list of
        strings. Defaults to the decorated callable's `__name__`.
    title - The command title displayed in Text menu. Not in menu if None.
    hotkey - Preferred command hotkey tuple: `(<key char>, <key mask>)`.
        Ignored if title is None.
    is_enabled - A callable that returns a boolean value indicating if
        the command is enabled in the Text menu. Always enabled if None.
        Signature: `is_enabled(textview, sender)`.
    parse_args - A callable that takes a string and returns a sequence of
        arguments to be passed to the command as the `args` parameter.
        Defaults to `string.split`. Signature: `parse_args(command_text)`.
        May return `None` if arguments cannot be parsed or are not recognized.
    lookup_with_parse_args - If True, use the `parse_args` callable to
        lookup the command. The command's argument parser should return None
        if it receives a text string that cannot be executed.
"""
import logging
from AppKit import NSCommandKeyMask, NSControlKeyMask, NSAlternateKeyMask
from editxt.textcommand import command

log = logging.getLogger(__name__)

def load_commands():
    return [test_command]

@command(hotkey=('T', NSCommandKeyMask | NSAlternateKeyMask))
def test_command(textview, sender, args):
    """Test Command

    This command sends a message to the log.
    """
    log.info('this is a test (args=%r)', args)
