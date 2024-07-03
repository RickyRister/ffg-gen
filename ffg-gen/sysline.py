from dataclasses import dataclass
from functools import cache
import re
import configs
from characterinfo import CharacterInfo


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
            raise ValueError(f'Invalid args for @expr: {args}')


@dataclass
class CharEnter(SysLine):
    """Forces the character to enter the screen.
    By default, all characters will start offscreen and won't enter until explicitly declared

    Usage: @exit [name]
    """

    name: str

    def parseArgs(args: str):
        match args.split():
            case [name]: return CharEnter(name=name.lower())
            case _: raise ValueError(f'Invalid args for @enter: {args}')


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
            case _: raise ValueError(f'Invalid args for @exit: {args}')


@dataclass
class Wait(SysLine):
    """Makes nothing happen for the next x seconds.
    Usage @wait [seconds]
    """

    duration: float

    def parseArgs(args: str):
        match args.split():
            case [duration]: return Wait(duration=float(duration))
            case _: raise ValueError(f'Invalid args for @wait: {args}')


@dataclass
class SetCharProperty(SysLine):
    '''Directly modifies the CharacterInfo of a character.
    The change will stick until a character cache reset happens.
    The symbol to use instead of '=' can be changed in the configs

    Usage: @set [name] [property]=[value]
    '''

    name: str       # character to modify for
    property: str   # the CharacterInfo property to modify
    value: str      # the value to set the property to

    def parseArgs(args: str):
        match args.split(1):
            case [name, modification]:
                match modification.split(configs.PARSING.assignmentDelimiter, 1):
                    case [property, value]: return SetCharProperty(name, property, value)
        ValueError(f'Invalid args for @set: {args}')

    def execute(self):
        '''Executes this sysline; does the modification
        '''
        charInfo = CharacterInfo.ofName(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(charInfo, self.property):
            raise ValueError(
                f'Failure with @set; CharacterInfo does not have property {self.property}')

        # possible type conversions
        # self.value starts as a string
        curr_value = getattr(charInfo, self.property)
        
        value = self.value
        if isinstance(curr_value, int):
            value = int(value)
        elif isinstance(curr_value, float):
            value = float(value)

        setattr(charInfo, self.property, value)


def parse_sysline(line: str):
    """Parses a sysline.

    args:
        line - a sysline with the @ stripped off already
    """

    match(line.split(None, 1)):
        case ('expression', args): return SetExpr.parseArgs(args.strip())
        case ('enter', args): return CharEnter.parseArgs(args.strip())
        case ('exit', args): return CharExit.parseArgs(args.strip())
        case ('wait', args): return Wait.parseArgs(args.strip())
        case ('set', args): return SetCharProperty.parseArgs(args.strip())
        case _:
            raise ValueError(f'Failure while parsing due to invalid sysline: {line}')
