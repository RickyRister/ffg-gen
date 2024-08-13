import re
from dataclasses import dataclass
from bio_gen.bioline import Line


@dataclass
class SysLine(Line):
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