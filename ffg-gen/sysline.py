from dataclasses import dataclass
import re


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
    Usage: @expr [name] [expression]
    """

    name: str
    expression: str

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 2:
            raise ValueError(f'Invalid args for command @expr: {args}')
        return SetExpr(name=splits[0], expression=splits[1])


def parse_sysline(line: str):
    """Parses a sysline.
    Syslines should begin being @. This function will assume it's true and won't double check!
    """

    command, args = line.split(None, 1)

    match(command):
        case '@expr': return SetExpr.parseArgs(args)
        case _:
            raise ValueError(f'Failure while parsing: invalid command {command} in sysline: {line}')
