import re
from dataclasses import dataclass

from vidpy.utils import Frame

import durations
from configcontext import ConfigContext
from exceptions import LineParseError
from lines import TextLine, SysLine, parse_common_sysline
from . import dconfigs


@dataclass
class DialogueLine(TextLine):
    '''A single parsed line from the script.
    The fields are parsed by using the regex in the config json.
    only the expression field is optional
    '''
    name: str
    expression: str | None
    text: str
    duration: Frame = None

    def __post_init__(self):
        if self.duration is None:
            self.duration = dconfigs.DURATIONS.calc_duration(self.text)


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
        case ['enter', args]: return CharEnter.parseArgs(args.strip())
        case ['enterall']: return CharEnterAll()
        case ['enterall', args]: return CharEnterAll.parseArgs(args.strip())
        case ['exit', args]: return CharExit.parseArgs(args.strip())
        case ['exitall']: return CharExitAll()
        case ['exitall', args]: return CharExitAll.parseArgs(args.strip())
        case ['sleep', args]: return Sleep.parseArgs(args.strip())
        case ['nick', args]: return Nick.parseArgs(args.strip())
        case ['unnick', args]: return UnNick.parseArgs(args.strip())
        case ['nametag', args]: return Nametag.parseArgs(args.strip())
        case ['front', args]: return Front.parseArgs(args.strip())
        case _: raise LineParseError(f'Unrecognized sysline: {line}')


# ===========================
# Dialogue-specific Syslines
# ===========================

@dataclass
class SetExpr(SysLine):
    """Sets the expression for a character.
    Usage: @expression [name] [expression]
    """

    name: str
    expression: str

    def parseArgs(args: str):
        if (matches := re.match(dconfigs.PARSING.expressionRegex, args)):
            return SetExpr(
                name=matches.group('name').lower().strip(),
                expression=matches.group('expression').strip())
        else:
            raise LineParseError(f'Invalid args for @expr: {args}')


@dataclass
class CharEnter(SysLine):
    """Forces the character to enter the screen.
    By default, all characters will start offscreen and won't enter until explicitly declared

    Usage: @enter [name]
    """

    name: str

    def parseArgs(args: str):
        match args.split():
            case [name]: return CharEnter(name=name.lower())
            case _: raise LineParseError(f'Invalid args for @enter: {args}')


@dataclass
class CharEnterAll(SysLine):
    """Forces all characters to enter the screen.
    Optionally lets you only affect the characters on a given side.

    Usage: @enterall <side>
    """
    is_player: bool = None

    def parseArgs(args: str):
        match args:
            case 'player' | 'players': return CharEnterAll(True)
            case 'enemy' | 'enemies': return CharEnterAll(False)
            case _: raise LineParseError(f'Invalid args for @enterall: {args}')


@dataclass
class CharExit(SysLine):
    """Forces the character to exit the screen.
    By default, all characters will automatically exit at the end of the scene

    Usage: @exit [name]
    """

    name: str

    def parseArgs(args: str):
        match args.split():
            case [name]: return CharExit(name=name.lower())
            case _: raise LineParseError(f'Invalid args for @exit: {args}')


@dataclass
class CharExitAll(SysLine):
    """Forces all characters to exit the screen.
    Optionally lets you only affect the characters on a given side.

    Usage: @exitall <side>
    """
    is_player: bool = None

    def parseArgs(args: str):
        match args:
            case 'player' | 'players': return CharExitAll(True)
            case 'enemy' | 'enemies': return CharExitAll(False)
            case _: raise LineParseError(f'Invalid args for @exitall: {args}')


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
class Nick(SysLine):
    '''Basically a shorthand for @alias [name] [alias] + @set [name] displayName [alias]
    Nicks are tracked separately, so that an unnick doesn't remove existing aliases

    Usage: @nick [name] [nickname]
    '''

    name: str
    nickname: str

    def parseArgs(args: str):
        match args.split():
            case [name, nickname]: return Nick(name, nickname)
            case _: raise LineParseError(f'Invalid args for @nick: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Set alias and set displayName
        '''
        context.add_local_alias(self.name, self.nickname)
        context.track_nick(self.name, self.nickname)

        charInfo = context.get_char(self.name)
        new_charInfo = charInfo.with_attr('displayName', self.nickname)
        context.update_char(new_charInfo)


@dataclass
class UnNick(SysLine):
    '''Undoes the effects of a @nick. 
    Unique in that it takes the original name instead of the nick, and won't remove existing aliases.

    Usage: @unnick [name]
    '''

    name: str

    def parseArgs(args: str):
        match args.split():
            case [name]: return UnNick(name)
            case _: raise LineParseError(f'Invalid args for @unnick: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Unset displayName and unset alias
        '''
        charInfo = context.get_char(self.name)
        new_charInfo = charInfo.with_reset_attr('displayName')
        context.update_char(new_charInfo)

        if (nickname := context.pop_nick(self.name)) is not None:
            context.remove_local_alias(nickname)


@dataclass
class Nametag(SysLine):
    '''Queues the start of a nametag animation

    Usage: @nametag [name]
    '''

    name: str

    def parseArgs(args: str):
        match args.split():
            case [name]: return Nametag(name)
            case _: raise LineParseError(f'Invalid args for @nametag: {args}')


@dataclass
class Front(SysLine):
    '''Forcibly brings the character to the front.
    The behavior is undefined if multiple characters are eligible to be brought to front.

    Usage: @front [name]
    '''

    name: str

    def parseArgs(args: str):
        match args.split():
            case [name]: return Front(name)
            case _: raise LineParseError(f'Invalid args for @front: {args}')
