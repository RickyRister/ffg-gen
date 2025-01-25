from dataclasses import dataclass

from vidpy.utils import Frame

import durations
from exceptions import LineParseError
from lines import TextLine, SysLine, parse_common_sysline
from mlt_resource import MltResource
from . import econfigs


@dataclass
class TextLine(TextLine):
    '''A parsed text block from the script.

    The text can contain newlines.

    The speaker is not recorded in the line, 
    since a single line from a speaker can span multiple EndingLines.
    The speaker is determined dynamically when generating from the lines.
    '''
    text: str
    duration: Frame = None

    def __post_init__(self):
        if self.duration is None:
            self.duration = econfigs.DURATIONS.calc_duration(self.text)


@dataclass
class PageTurn(SysLine):
    '''Represents a "page turn" of the dialogue
    '''


# ========================
# Ending-specific Syslines
# ========================

def parse_sysline(line: str) -> SysLine:
    """Parses a sysline.

    args:
        line - a sysline with the @ stripped off already
    """
    sysline = parse_common_sysline(line)
    if sysline is not None:
        return sysline

    match line.split(None, 1):
        case ['wait', args]: return Wait.parseArgs(args.strip())
        case ['sleep', args]: return Sleep.parseArgs(args.strip())
        case ['speaker', args]: return SetSpeaker.parseArgs(args.strip())
        case ['bgimage', args]: return SetBgImage.parseArgs(args.strip())
        case _: raise LineParseError(f'Unrecognized sysline: {line}')


@dataclass
class Wait(SysLine):
    """Makes the preceeding text line stay for longer.
    Interprets integer durations as frames and float durations as seconds.

    Usage: @wait [duration]
    """

    duration: Frame

    def parseArgs(args: str):
        match args.split():
            case [duration]: return Wait(durations.to_frame(duration))
            case _: raise LineParseError(f'Invalid args for @wait: {args}')


@dataclass
class Sleep(SysLine):
    """Makes nothing happen for the given duration.
    `tfill` components will not display during this time.
    Interprets integer durations as frames and float durations as seconds.

    Usage: @sleep [duration]
    """

    duration: Frame

    def parseArgs(args: str):
        match args.split():
            case [duration]: return Sleep(durations.to_frame(duration))
            case _: raise LineParseError(f'Invalid args for @sleep: {args}')


@dataclass
class SetSpeaker(SysLine):
    '''Sets the current speaker
    Usage: @speaker [name]
    '''

    name: str | None

    def parseArgs(args: str):
        match args.split(None, 1):
            case [name]: return SetSpeaker(name)
            case _: raise LineParseError(f'Invalid args for @speaker: {args}')


@dataclass
class SetBgImage(SysLine):
    '''Sets the current bg image.
    Usage: `@bgimage [image]`

    `@bgimage none` to unset the image
    '''

    image: MltResource | None

    def parseArgs(args: str):
        match args:
            case 'none': return SetBgImage(None)
            case image: return SetBgImage(MltResource(image))
