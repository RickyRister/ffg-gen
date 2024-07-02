from dataclasses import dataclass


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

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 2:
            raise ValueError(f'Invalid args for command @expr: {args}')
        return SetExpr(name=splits[0].lower(), expression=splits[1])


@dataclass
class CharEnter(SysLine):
    """Forces the character to enter the screen.
    By default, all characters will enter at the start. 
    Call @exit before the first line to make the character start offscreen.
    Usage: @exit [name]
    """

    name: str

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 1:
            raise ValueError(f'Invalid args for command @enter: {args}')
        return CharExit(name=splits[0].lower())


@dataclass
class CharExit(SysLine):
    """Forces the character to exit the screen.
    By default, all characters will enter at the start. 
    Call @exit before the first line to make the character start offscreen.
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

    seconds: float

    def parseArgs(args: str):
        splits = args.split()
        if len(splits) != 1:
            raise ValueError(f'Invalid args for command @wait: {args}')
        return Wait(seconds=float(splits[0]))


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
