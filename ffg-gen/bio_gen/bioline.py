from dataclasses import dataclass

from vidpy.utils import Frame

from exceptions import LineParseError
from lines import TextLine, SysLine, parse_common_sysline
from . import bconfigs


@dataclass
class BioTextBlock(TextLine):
    '''A single parsed text block from the script.
    Note that this can represent multiple actual lines in the script.
    We still treat this thing as a single "line" when processing
    '''
    name: str | None
    text: str
    pagenum: int
    total_pages: int | None = None  # this field is set on the second pass
    duration: Frame = None

    def __post_init__(self):
        if self.duration is None:
            self.duration = bconfigs.DURATIONS.calc_duration(self.text)


# ======================
# Bio-specific Syslines
# ======================

def parse_sysline(line: str) -> SysLine:
    """Parses a sysline.

    args:
        line - a sysline with the @ stripped off already
    """
    sysline = parse_common_sysline(line)
    if sysline is not None:
        return sysline

    match line.split(None, 1):
        case ['expression', args]: return SetExpr.parseArgs(args.strip())
        case _: raise LineParseError(f'Unrecognized sysline: {line}')


@dataclass
class SetExpr(SysLine):
    """Sets the expression for a character.
    Usage: @expression [name] [expression]
    """

    name: str
    expression: str

    def parseArgs(args: str):
        match args.split(None, 1):
            case [name, expression]: return SetExpr(name, expression)
            case _: raise LineParseError(f'Invalid args for @expr: {args}')
