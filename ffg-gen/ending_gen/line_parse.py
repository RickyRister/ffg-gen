from enum import Enum, auto
from typing import Iterable, Generator
from lines import Line
from ending_gen.endingline import TextLine, PageTurn, parse_sysline


def parse_ending_file(lines: Iterable[str]) -> list[Line]:
    '''Parse the script into the internal representation.
    The output is given as a list of Lines.

    (We might add chapter support in the future)
    '''
    return list(parse_lines(lines))


def parse_lines(lines: list[str]) -> Generator[Line, None, None]:
    r''' This is a generator because bio line parsing needs to be stateful.

    ### Parsing Logic:
    Any line that isn't one of the below exceptions will be interpreted as a text line.
    Any text line that ends with `\` will continue on to the next line.
    The line break will be stored in the Line's text string.
    There is currently no escape.

    `@`: is always interpreted as a sysline. There is currently no escape

    `---`: ends the current block. Is tracked as a sysline.

    `//`: is always a comment. There is currently no escape.

    Empty lines will always be skipped. There is currently no escape.

    Speaker name is treated no different when parsing.
    Speaker tracking will be handled when generating.
    '''
    # used to store lines for multi-line texts
    buffer: list[str] = []

    for line in lines:
        # strip right before processing
        # we preserve left whitespace since multi-line text might care about it
        line = line.rstrip()

        # skip this line if it's empty or it's a comment
        if isComment(line):
            continue

        # process this line as a sysline if it begins with @
        elif (line.startswith('@')):
            yield parse_sysline(line[1:])

        # `---` always marks a page turn
        elif (line.startswith('---')):
            yield PageTurn()

        # process line as normal text
        else:
            # add text to buffer if multi-line
            if line.endswith('\\'):
                buffer.append(line[:-1])

            # finally yield the Line
            else:
                text: str
                if len(buffer) == 0:
                    text = line
                # flush buffer if not empty
                else:
                    buffer.append(line)
                    text = str.join('\n', buffer)
                    buffer.clear()
                yield TextLine(text)


def isComment(line: str) -> bool:
    return len(line) == 0 or line.startswith('//')
