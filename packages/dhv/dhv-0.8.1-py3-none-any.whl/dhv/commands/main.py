"""Provides the main commands for the application."""

##############################################################################
# Textual enhanced imports.
from textual_enhanced.commands import Command


##############################################################################
class NewCode(Command):
    """Empty the editor ready to enter some new code"""

    BINDING_KEY = "ctrl+n"
    SHOW_IN_FOOTER = True
    FOOTER_TEXT = "New"


##############################################################################
class LoadFile(Command):
    """Load the content of a Python source file"""

    BINDING_KEY = "ctrl+l"
    SHOW_IN_FOOTER = True
    FOOTER_TEXT = "Load"


##############################################################################
class SwitchLayout(Command):
    """Switch the screen layout between horizontal and vertical"""

    BINDING_KEY = "f2"


##############################################################################
class ShowDisassemblyOnly(Command):
    """Only show the disassembly of the source code"""

    BINDING_KEY = "ctrl+b"


##############################################################################
class ShowASTOnly(Command):
    """Only show the AST of the source code"""

    BINDING_KEY = "ctrl+t"


##############################################################################
class ShowDisassemblyAndAST(Command):
    """Show both the disassembly and the AST of the source code"""

    BINDING_KEY = "ctrl+o"


##############################################################################
class ChangeCodeTheme(Command):
    """Change the theme of the Python code editor"""

    BINDING_KEY = "ctrl+f9"


##############################################################################
class OpcodeCounts(Command):
    """View the count of opcodes in the code"""

    BINDING_KEY = "f5"
    SHOW_IN_FOOTER = True


### main.py ends here
