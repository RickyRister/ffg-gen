from typing import Any
from dataclasses import dataclass
import ast
from exceptions import NonExistentProperty
from bio_gen.bioline import Line
from bio_gen.bioinfo import BioInfo
from bio_gen.configcontext import ConfigContext


@dataclass
class SysLine(Line):
    """Parent class for sys lines.
    Sys line stands for System Line.
    Syslines act as commands in the dialogue file.
    Syslines begin with @

    DialogueLine and some Sysline subclasses both share a name attribute.
    You can check that attribute if you need to get the target of an action. 
    """

    def pre_hook(self, context: ConfigContext):
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
        case ['set', args]: return SetCharProperty.parseArgs(args.strip())
        case ['unset', args]: return UnsetCharProperty.parseArgs(args.strip())
        case ['reset', args]: return ResetCharProperties.parseArgs(args.strip())
        case ['resetall']: return ResetAllChars()
        case ['component', args]: return GroupedComponent.parseArgs(args.strip())
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
        match args.split(None, 1):
            case [name, expression]: return SetExpr(name, expression)
            case _: raise ValueError(f'Invalid args for @expr: {args}')


@dataclass
class SetCharProperty(SysLine):
    '''Directly modifies the BioInfo of a character.
    The change will stick until a character cache reset happens.

    Usage: @set [name] [property] [value]
    '''

    name: str       # character to modify for
    property: str   # the BioInfo property to modify
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

    def pre_hook(self, context: ConfigContext):
        '''Does the modification
        '''
        bioInfo = context.get_char(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(bioInfo, self.property):
            raise NonExistentProperty(
                f'Failed to @set {self.name} {self.property} {self.value}; BioInfo does not have property {self.property}')

        new_charInfo = bioInfo.with_attr(self.property, self.value)
        context.update_char(new_charInfo)


@dataclass
class UnsetCharProperty(SysLine):
    '''Unsets the field in the BioInfo of a character.
    The value will be back to what it was when loaded from config

    Usage: @unset [name] [property]
    '''

    name: str       # character to modify for
    property: str   # the BioInfo property to unset

    def parseArgs(args: str):
        match args.split():
            case [name, property]: return UnsetCharProperty(name, property)
            case _: raise ValueError(f'Invalid args for @unset: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Unsets the property
        '''
        bioInfo: BioInfo = context.get_char(self.name)

        # checks that the property actually exists, to safeguard against typos
        if not hasattr(bioInfo, self.property):
            raise ValueError(
                f'@unset {self.name} {self.property} failed; BioInfo does not have property {self.property}')

        new_charInfo = bioInfo.with_reset_attr(self.property)
        context.update_char(new_charInfo)


@dataclass
class ResetCharProperties(SysLine):
    '''Unsets all fields in the BioInfo of a character.
    The value will be back to what it was when loaded from config

    Usage: @reset [name]
    '''

    name: str       # character to reset

    def parseArgs(args: str):
        match args.split():
            case [name]: return ResetCharProperties(name)
            case _: raise ValueError(f'Invalid args for @unset: {args}')

    def pre_hook(self, context: ConfigContext):
        '''Resets the BioInfo
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
            case _: raise ValueError(f'Invalid args for @component: {args}')
