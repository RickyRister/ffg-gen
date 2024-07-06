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

    DialogueLine and some Sysline subclasses both share a name attribute.
    You can check that attribute if you need to get the target of an action. 
    """

    def pre_hook(self):
        '''Put code here that should always be run regardless of line processing logic.
        Processors should always call this on every sysline, before line processing.
        '''
        pass


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

    Usage: @enter [name]
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

    Usage: @set [name] [property] [value]
    '''

    name: str       # character to modify for
    property: str   # the CharacterInfo property to modify
    value: str      # the value to set the property to

    def parseArgs(args: str):
        match args.split(None, 2):
            case [name, property, value]: return SetCharProperty(name, property, value)
            case _: raise ValueError(f'Invalid args for @set: {args}')

    def pre_hook(self):
        '''Does the modification
        '''
        charInfo = CharacterInfo.ofName(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(charInfo, self.property):
            raise ValueError(
                f'@set {self.name} {self.property}{configs.PARSING.assignmentDelimiter}{self.value} failed; CharacterInfo does not have property {self.property}')

        # possible type conversions
        # self.value starts as a string
        curr_value = getattr(charInfo, self.property)

        value = self.value
        if isinstance(curr_value, float) or isinstance(curr_value, int):
            try:
                value = int(value)
            except ValueError:
                value = float(value)

        setattr(charInfo, self.property, value)


@dataclass
class UnsetCharProperty(SysLine):
    '''Unsets the field in the CharacterInfo of a character.
    The value will be back to what it was when loaded from config

    Usage: @unset [name] [property]
    '''

    name: str       # character to modify for
    property: str   # the CharacterInfo property to unset

    def parseArgs(args: str):
        match args.split():
            case [name, property]: return UnsetCharProperty(name, property)
            case _: raise ValueError(f'Invalid args for @unset: {args}')

    def pre_hook(self):
        '''Unsets the property
        '''
        charInfo: CharacterInfo = CharacterInfo.ofName(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(charInfo, self.property):
            raise ValueError(
                f'@unset {self.name} {self.property} failed; CharacterInfo does not have property {self.property}')

        charInfo.reset_attr(self.property)


@dataclass
class ResetCharProperties(SysLine):
    '''Unsets all fields in the CharacterInfo of a character.
    The value will be back to what it was when loaded from config

    Usage: @reset [name]
    '''

    name: str       # character to reset

    def parseArgs(args: str):
        match args.split():
            case [name]: return ResetCharProperties(name)
            case _: raise ValueError(f'Invalid args for @unset: {args}')

    def pre_hook(self):
        '''Resets the CharacterInfo
        '''
        CharacterInfo.ofName(self.name).reset_all_attr()


@dataclass
class ResetAllChars(SysLine):
    '''Resets the character cache, causing all set properties to be reset for all characters.

    Usage: @resetall
    '''

    def pre_hook(self):
        '''Does the cache reset
        '''
        CharacterInfo.get_cached.cache_clear()


def parse_sysline(line: str):
    """Parses a sysline.

    args:
        line - a sysline with the @ stripped off already
    """

    match line.split(None, 1):
        case ['expression', args]: return SetExpr.parseArgs(args.strip())
        case ['enter', args]: return CharEnter.parseArgs(args.strip())
        case ['exit', args]: return CharExit.parseArgs(args.strip())
        case ['wait', args]: return Wait.parseArgs(args.strip())
        case ['set', args]: return SetCharProperty.parseArgs(args.strip())
        case ['unset', args]: return UnsetCharProperty.parseArgs(args.strip())
        case ['reset', args]: return ResetCharProperties.parseArgs(args.strip())
        case ['resetall']: return ResetAllChars()
        case _:
            raise ValueError(f'Failure while parsing due to invalid sysline: {line}')
