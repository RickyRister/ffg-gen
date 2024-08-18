import ast
from abc import ABC
from typing import Any
from dataclasses import dataclass
from configcontext import ConfigContext
from exceptions import NonExistentPropertyError, LineParseError


@dataclass
class Line(ABC):
    '''Represents a parsed line from the script.

    Has no functionality on its own.
    Just here so we have a type to group the various line types under 
    to make it easier for type hinting
    '''


@dataclass
class TextLine(Line):
    '''Represents a line that contains text.
    A TextLine should have a text attr and a duration attr
    '''


@dataclass
class SysLine(Line):
    '''Parent class for sys lines.
    Sys line stands for System Line.
    Syslines act as commands in the dialogue file.
    Syslines begin with @

    Textline and some Sysline subclasses both share a name attribute.
    You can check that attribute if you need to get the target of an action. 

    Textline and some Sysline subclasses both share a name duration.
    You can check that attribute to determine if the line takes up actual space as a clip.
    '''

    def pre_hook(self, context: ConfigContext):
        '''Put code here that should always be run regardless of line processing logic.
        Processors should always call this on every sysline, before line processing.
        '''
        pass


# ================
# Common Syslines
# ================

def parse_common_sysline(line: str) -> SysLine | None:
    '''Parses a common sysline.
    Returns None if the line isn't recognized, so you can do more specific parsing.

    args:
        line - a sysline with the @ stripped off already
    returns: 
        The parsed sysline, or None if the sysline isn't recognized
    '''

    match line.split(None, 1):
        case ['set', args]: return SetCharProperty.parseArgs(args.strip())
        case ['unset', args]: return UnsetCharProperty.parseArgs(args.strip())
        case ['reset', args]: return ResetCharProperties.parseArgs(args.strip())
        case ['resetall']: return ResetAllChars()
        case ['alias', args]: return SetAlias.parseArgs(args.strip())
        case ['unalias', args]: return UnsetAlias.parseArgs(args.strip())
        case ['component', args]: return GroupedComponent.parseArgs(args.strip())
        case _: return None


@dataclass
class SetCharProperty(SysLine):
    '''Directly modifies the Info of a character.
    The change will stick until a character cache reset happens.

    Usage: @set [name] [property] [value]
    '''

    name: str       # character to modify for
    property: str   # the Info property to modify
    value: Any      # the value to set the property to

    def parseArgs(args: str):
        match args.split(None, 2):
            case [name, property, value]:
                try:
                    parsed_value: Any = ast.literal_eval(value)
                    return SetCharProperty(name, property, parsed_value)
                except (LineParseError, SyntaxError):
                    raise LineParseError(
                        f'Invalid args for @set {args}; {value} is not a valid python literal.')
            case _: raise LineParseError(f'Invalid args for @set: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Does the modification
        '''
        info = context.get_char(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(info, self.property):
            raise NonExistentPropertyError(
                f'Failed to @set {self.name} {self.property} {self.value}; Info does not have property {self.property}')

        new_charInfo = info.with_attr(self.property, self.value)
        context.update_char(new_charInfo)


@dataclass
class UnsetCharProperty(SysLine):
    '''Unsets the field in the Info of a character.
    The value will be back to what it was when loaded from config

    Usage: @unset [name] [property]
    '''

    name: str       # character to modify for
    property: str   # the Info property to unset

    def parseArgs(args: str):
        match args.split():
            case [name, property]: return UnsetCharProperty(name, property)
            case _: raise LineParseError(f'Invalid args for @unset: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Unsets the property
        '''
        info = context.get_char(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(info, self.property):
            raise LineParseError(
                f'@unset {self.name} {self.property} failed; Info does not have property {self.property}')

        new_charInfo = info.with_reset_attr(self.property)
        context.update_char(new_charInfo)


@dataclass
class ResetCharProperties(SysLine):
    '''Unsets all fields in the Info of a character.
    The value will be back to what it was when loaded from config

    Usage: @reset [name]
    '''

    name: str       # character to reset

    def parseArgs(args: str):
        match args.split():
            case [name]: return ResetCharProperties(name)
            case _: raise LineParseError(f'Invalid args for @unset: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Resets the Info
        '''
        context.reset_char(self.name)


@dataclass
class ResetAllChars(SysLine):
    '''Resets the character cache, causing all set properties to be reset for all characters.

    Usage: @resetall
    '''

    def pre_hook(self, context: ConfigContext):
        '''Does the cache reset
        '''
        context.reset_all_char()


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
            case _: raise LineParseError(f'Invalid args for @alias: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Set alias
        '''
        context.add_local_alias(self.name, self.alias)


@dataclass
class UnsetAlias(SysLine):
    '''Unset a local alias for a character.

    Usage: @unalias [alias]
    '''

    alias: str

    def parseArgs(args: str):
        match args.split():
            case [alias]: return UnsetAlias(alias)
            case _: raise LineParseError(f'Invalid args for @unalias: {args}')

    def pre_hook(self, context: ConfigContext):
        '''unset alias
        '''
        context.remove_local_alias(self.alias)


@dataclass
class GroupedComponent(SysLine):
    '''Used by the group:[group] and groups component to recursively generate components.
    Not used during actual generation processing.

    Usage: @component [group] [component]
    '''

    group: str
    component: str

    def parseArgs(args: str):
        match args.split(None, 1):
            case [group, component]: return GroupedComponent(group, component)
            case _: raise LineParseError(f'Invalid args for @component: {args}')
