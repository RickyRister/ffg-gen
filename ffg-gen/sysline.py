from dataclasses import dataclass
from functools import cache
import re
import configs


@dataclass
class SysLine:
    """Parent class for sys lines.
    Sys line stands for System Line.
    Syslines act as commands in the dialogue file.
    Syslines begin with @
    """


@dataclass
class SetExpr(SysLine):
    """Sets the expression for a character.
    Usage: @expression [name] [expression]
    """

    name: str
    expression: str

    @cache
    def getExpressionRegex() -> re.Pattern:
        """We have this in a separate function so we can cache the result and don't have to recompile every time
        """
        return re.compile(configs.PARSING.expressionRegex)

    def parseArgs(args: str):
        if (matches := SetExpr.getExpressionRegex().match(args)):
            return SetExpr(
                name=matches.group('name').lower().strip(),
                expression=matches.group('expression').strip())
        else:
            raise ValueError(f'Invalid args for command @expr: {args}')


@dataclass
class CharEnter(SysLine):
    """Forces the character to enter the screen.
    By default, all characters will start offscreen and won't enter until explicitly declared

    Usage: @exit [name]
    """

    name: str

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 1:
            raise ValueError(f'Invalid args for command @enter: {args}')
        return CharEnter(name=splits[0].lower())


@dataclass
class CharExit(SysLine):
    """Forces the character to exit the screen.
    By default, all characters will automatically exit at the end of the scene

    Usage: @exit [name]
    """

    name: str

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 1:
            raise ValueError(f'Invalid args for command @exit: {args}')
        return CharExit(name=splits[0].lower())


@dataclass
class Wait(SysLine):
    """Makes nothing happen for the next x seconds.
    Usage @wait [seconds]
    """

    duration: float

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 1:
            raise ValueError(f'Invalid args for command @wait: {args}')
        return Wait(duration=float(splits[0]))


def parse_sysline(line: str):
    """Parses a sysline.
    Syslines should begin being @. This function will assume it's true and won't double check!
    """

    command, args = line.split(None, 1)

    match(command):
        case '@expression': return SetExpr.parseArgs(args)
        case '@enter': return CharEnter.parseArgs(args)
        case '@exit': return CharExit.parseArgs(args)
        case '@wait': return Wait.parseArgs(args)
        case _:
            raise ValueError(f'Failure while parsing: invalid command {command} in sysline: {line}')
