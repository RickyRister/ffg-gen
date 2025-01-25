import re
from dataclasses import dataclass
from typing import Iterable, Generator

import configs
from dialogue_gen.dialogueline import DialogueLine, parse_sysline
from durations import Frame, to_frame
from exceptions import LineParseError, DialogueGenException
from lines import Line
from . import dconfigs


@dataclass
class ChapterLine:
    '''Indicates the start of a new chapter
    '''
    name: str


def parseDialogueFile(lines: Iterable[str]) -> tuple[list[Line], dict[str, list[Line]]]:
    """Parse the script into the internal representation
    The output is given as a tuple of (common, dict[chapters])
    """
    # parse all lines
    parsed = list(parse_lines(lines))

    # get indexes of all chapter markers
    chapter_indexes = [i for i, line in enumerate(parsed) if isinstance(line, ChapterLine)]
    chapter_indexes.append(len(parsed))     # append final index to make iteration logic easier

    # get common lines (goes from start to first chapter marker)
    common_lines = parsed[0:chapter_indexes[0]]

    # build chapter map
    # parsed[start_index] gets ChapterLine; parsed[start_index+1: end_index] gets all Lines until the next chapter
    chapters = {parsed[start_index].name: parsed[start_index+1: end_index]
                for start_index, end_index in iterate_by_pairs(chapter_indexes)}

    return common_lines, chapters


def iterate_by_pairs(iterable: Iterable) -> Generator[tuple[int, int], None, None]:
    '''[1 2 3 4] -> (1 2), (2 3), (3 4)
    '''
    if len(iterable) < 2:
        return

    second = iterable[0]
    for next_item in iterable[1:]:
        first = second
        second = next_item
        yield first, second


def parse_lines(lines: str) -> Generator[Line, None, None]:
    '''Parse all the lines in the file.
    '''
    pending_directives: list[Directive] = []

    for line in lines:
        # strip before processing
        line = line.strip()

        # skip this line if it's empty or it's a comment
        if (isComment(line)):
            continue

        # process this line as a sysline if it begins with @
        if (line.startswith('@')):
            yield parse_sysline(line[1:])
            continue

        # process this line as a chapter marker if it begins with ===
        if (line.startswith('===')):
            yield ChapterLine(line.removeprefix('===').strip())
            continue

        # process this line as a line parse directive if it begins with !
        if (line.startswith('!')):
            if (directive := parse_directive(line[1:])) is not None:
                pending_directives.append(directive)
            continue

        expression: str = None

        # try to match normal dialogue line
        match = re.match(dconfigs.PARSING.dialogueRegex, line)
        if match:
            expression = match.group('expression').strip()  # normal dialogue line exclusive group
        else:
            # try to match shortened dialogue line and throw if that match also fails
            if not (match := re.match(dconfigs.PARSING.shortDialogueRegex, line)):
                raise LineParseError(f'Unrecognized line: {line}')

        # groups that appear in both dialogue line types
        name = match.group('name').strip().lower()
        text = match.group('text').strip()

        # process match into a dialogueLine
        dialogueLine = DialogueLine(name, expression, text)

        # apply any pending directives and reset the directive list
        for directive in pending_directives:
            directive.apply(dialogueLine)

        pending_directives.clear()

        yield dialogueLine


def isComment(line: str) -> bool:
    return len(line) == 0 or line.startswith('#') or line.startswith('//') or line.startswith('(')


#
# Line parse directives
#

@dataclass
class Directive:
    '''Abstract base class for Directive lines
    '''

    def apply(self, line: DialogueLine) -> None: ...


def parse_directive(line: str) -> Directive | None:
    match line.split(None, 1):
        case ['dur', args]: return Dur.parseArgs(args.strip())
        case ['define', args]: Define.parseArgs(args.strip())
        case _: raise LineParseError(f'Unrecognized directive: {line}')


@dataclass
class Dur(Directive):
    ''' Affects the duration of the next DialogueLine.

    Usage example: !dur +1.0

    Give frames in integers and seconds in floats.
    Putting a `+` or `-` in front will add that much duration.
    Otherwise it directly overwrites the duration. 
    '''
    operation: str   # one of +, - , =
    value: Frame

    @staticmethod
    def parseArgs(line: str) -> Directive:
        match line[0]:
            case '+': return Dur('+', to_frame(line[1:]))
            case '-': return Dur('-', to_frame(line[1:]))
            case _: return Dur('=', to_frame(line))

    def apply(self, line: DialogueLine) -> None:
        new_duration: Frame = None
        match self.operation:
            case '=': new_duration = self.value
            case '+': new_duration = line.duration + self.value
            case '-': new_duration = line.duration - self.value

        if new_duration <= 0:
            raise DialogueGenException(
                f'Dialogue line will have negative duration after applying {self}: {line}')

        line.duration = new_duration


@dataclass
class Define(Directive):
    ''' Modifies the global named resources dictionary. 
    Yes, I know this is really bad practice. I just don't feel like finding a better way right now.

    Usage example: !define stage_folder _textless/s1/
    '''

    @staticmethod
    def parseArgs(line: str) -> None:
        match line.split(None, 1):
            case [name, value]: configs.RESOURCE_NAMES[name] = value
            case _: LineParseError(f'Unrecognized !define directive: {line}')
