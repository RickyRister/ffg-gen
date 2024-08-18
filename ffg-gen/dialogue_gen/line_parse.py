from dataclasses import dataclass
from typing import Iterable, Generator
import re
from lines import Line
from . import dconfigs
from dialogue_gen.dialogueline import DialogueLine, parse_sysline
from exceptions import LineParseError


@dataclass
class ChapterLine:
    '''Indicates the start of a new chapter
    '''
    name: str


def parseDialogueFile(lines: Iterable[str]) -> tuple[list[Line], dict[str, list[Line]]]:
    """Parse the script into the internal representation
    The output is given as a tuple of (common, dict[chapters])
    """
    # parse all lines and filter out empty lines
    parsed = [parseLine(line) for line in lines]
    parsed = [line for line in parsed if line is not None]

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


def parseLine(line: str) -> Line | ChapterLine | None:
    """Parse a single line of the file
    """
    # strip before processing
    line = line.strip()

    # skip this line if it's empty or it's a comment
    if (isComment(line)):
        return None

    # process this line as a sysline if it begins with @
    if (line.startswith('@')):
        return parse_sysline(line[1:])

    # process this line as a chapter marker if it begins with ===
    if (line.startswith('===')):
        return ChapterLine(line.removeprefix('===').strip())

    text: str = None
    name: str = None
    expression: str = None

    # try to match normal dialogue line
    match = re.match(dconfigs.PARSING.dialogueRegex, line)
    if match:
        expression = match.group('expression').strip()  # normal dialogue line exclusive group
    else:
        # try to match shortened dialogue line and throw if that match also fails
        if not (match := re.match(dconfigs.PARSING.shortDialogueRegex, line)):
            raise LineParseError(f'line did not match regex exactly: {line}')

    # groups that appear in both dialogue line types
    name = match.group('name').strip().lower()
    text = match.group('text').strip()

    # process match into a dialogueLine
    return DialogueLine(name, expression, text)


def isComment(line: str) -> bool:
    return len(line) == 0 or line.startswith('#') or line.startswith('//') or line.startswith('(')
