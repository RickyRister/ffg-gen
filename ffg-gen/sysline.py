from dataclasses import dataclass
from typing import Any
import ast
import re
import configs
import alias
from characterinfo import CharacterInfo
from exceptions import NonExistentProperty


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
        case ['alias', args]: return SetAlias.parseArgs(args.strip())
        case ['unalias', args]: return UnsetAlias.parseArgs(args.strip())
        case ['nick', args]: return Nick.parseArgs(args.strip())
        case ['unnick', args]: return UnNick.parseArgs(args.strip())
        case ['grouped', args]: return GroupedComponent.parseArgs(args.strip())
        case _:
            raise ValueError(f'Failure while parsing due to invalid sysline: {line}')


@dataclass
class SetExpr(SysLine):
    """Sets the expression for a character.
    Usage: @expression [name] [expression]
    """

    name: str
    expression: str

    def parseArgs(args: str):
        if (matches := re.match(configs.PARSING.expressionRegex, args)):
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
    value: Any      # the value to set the property to

    def parseArgs(args: str):
        match args.split(None, 2):
            case [name, property, value]:
                try:
                    parsed_value: Any = ast.literal_eval(value)
                    return SetCharProperty(name, property, parsed_value)
                except (ValueError, SyntaxError):
                    raise ValueError(
                        f'Invalid args for @set {args}; {value} is not a valid python literal.')
            case _: raise ValueError(f'Invalid args for @set: {args}')

    def pre_hook(self):
        '''Does the modification
        '''
        charInfo = CharacterInfo.ofName(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(charInfo, self.property):
            raise NonExistentProperty(
                f'Failed to @set {self.name} {self.property} {self.value}; CharacterInfo does not have property {self.property}')

        setattr(charInfo, self.property, self.value)


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


@dataclass
class SetAlias(SysLine):
    '''Sets a local alias for a character. That means the alias can be used in place of the name.

    Usage: @alias [name] [alias]
    '''

    name: str
    alias: str

    def parseArgs(args: str):
        match args.split():
            case [name, alias]: return SetAlias(name, alias)
            case _: raise ValueError(f'Invalid args for @alias: {args}')

    def pre_hook(self):
        '''Set alias
        '''
        alias.add_local_alias(self.name, self.alias)


@dataclass
class UnsetAlias(SysLine):
    '''Unset a local alias for a character.

    Usage: @unalias [alias]
    '''

    alias: str

    def parseArgs(args: str):
        match args.split():
            case [alias]: return UnsetAlias(alias)
            case _: raise ValueError(f'Invalid args for @unalias: {args}')

    def pre_hook(self):
        '''unset alias
        '''
        alias.remove_local_alias(self.alias)


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
            case _: raise ValueError(f'Invalid args for @nick: {args}')

    def pre_hook(self):
        '''Set alias and set displayName
        '''
        alias.add_local_alias(self.name, self.nickname)
        alias.track_nick(self.name, self.nickname)
        charInfo: CharacterInfo = CharacterInfo.ofName(self.name)
        charInfo.displayName = self.nickname


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
            case _: raise ValueError(f'Invalid args for @unnick: {args}')

    def pre_hook(self):
        '''Unset displayName and unset alias
        '''
        charInfo: CharacterInfo = CharacterInfo.ofName(self.name)
        charInfo.reset_attr('displayName')
        if (nickname := alias.pop_nick(self.name)) is not None:
            alias.remove_local_alias(nickname)


@dataclass
class GroupedComponent(SysLine):
    '''Used by the group:[group] and groups component to recursively generate components.
    Not used during actual generation processing.

    Usage: @grouped [group] [component]
    '''

    group: str
    component: str

    def parseArgs(args: str):
        match args.split(None, 1):
            case [group, component]: return GroupedComponent(group, component)
            case _: raise ValueError(f'Invalid args for @grouped: {args}')
