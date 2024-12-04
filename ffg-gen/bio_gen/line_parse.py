from enum import Enum, auto
from typing import Iterable, Generator
from dataclasses import dataclass
import configs
from lines import Line
from exceptions import LineParseError, DialogueGenException
from durations import Frame, to_frame
from bio_gen.bioline import BioTextBlock, parse_sysline


@dataclass
class ChapterLine:
    '''Indicates the start of a new chapter
    '''
    name: str


class State(Enum):
    PENDING = auto()
    IN_BLOCK = auto()


def parse_bio_file(lines: Iterable[str]) -> tuple[list[Line], dict[str, list[Line]]]:
    '''Parse the script into the internal representation.
    The output is given as a tuple of (common, dict[chapters])
    '''
    # parse all lines
    parsed = list(parse_lines(lines))

    # set total_pages on all bio lines
    total_pagenum = len([line for line in parsed if isinstance(line, BioTextBlock)])
    for line in parsed:
        if isinstance(line, BioTextBlock):
            line.total_pages = total_pagenum

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


def isComment(line: str) -> bool:
    return len(line) == 0 or line.startswith('#') or line.startswith('//') or line.startswith('(')


def parse_lines(lines: Iterable[str]) -> Generator[Line, None, None]:
    '''This is a generator because bio line parsing needs to be stateful.

    ### Parsing Logic:
    We start off in pending state.
    While in pending state, comments and syslines are still processed.
    The next non-comment or sysline line will start a new text block.

    '---': Ends the current block and sets the state to pending.  

    '---*': Ends the current block and immediately starts a new text block.  
    Unlike the above, this will not set the state to pending.
    It immediately starts the text block on the next line.

    Syslines and comments are only processed outside of text blocks.
    They will be treated as raw text inside of text blocks.

    '===': Starts a new chapter, which will naturally end the current block.
    '''
    state: State = State.PENDING
    buffer: list[str] = []
    pagenum: int = 0
    pending_directives: list[Directive] = []

    def flush_buffer(curr_name: str | None) -> BioTextBlock:
        '''Joins all the accumulated lines into a text block, then clears the accumlator.
        Strips all trailing blank lines.
        '''
        # keep removing last line if it's blank
        while len(buffer) > 0 and not buffer[-1].strip():
            buffer.pop()

        # increment pagenum
        nonlocal pagenum
        pagenum += 1

        # create text block
        text: str = str.join('\n', buffer)
        textblock = BioTextBlock(curr_name, text, pagenum)

        # apply any pending directives
        for directive in pending_directives:
            directive.apply(textblock)

        # clear accumlators before returning
        buffer.clear()
        pending_directives.clear()

        return textblock

    # a character set during a text block start
    # will persist until another character is set
    curr_name: str = None

    for line in lines:
        # processing while in pending state
        if state is State.PENDING:
            # strip before processing
            line = line.strip()

            # skip this line if it's empty or it's a comment
            if isComment(line):
                continue

            # process this line as a sysline if it begins with @
            elif (line.startswith('@')):
                yield parse_sysline(line[1:])

            # process this line as a line parse directive if it begins with !
            elif (line.startswith('!')):
                if (directive := parse_directive(line[1:])) is not None:
                    pending_directives.append(directive)
                continue

            # '---*' immediately starts a new text block
            elif (line.startswith('---*')):
                state = State.IN_BLOCK
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('---*').strip()):
                    curr_name = char_name

            # '---' sets state to pending
            elif (line.startswith('---')):
                # we're already in pending state, but this line can also
                # change the character, so we still need to check that
                if (char_name := line.removeprefix('---').strip()):
                    curr_name = char_name

            # '===' ends the current chapter and starts a new one
            elif (line.startswith('===')):
                # we don't need to flush the buffer since we're in PENDING state
                yield ChapterLine(line.removeprefix('===').strip())

            # any other text starts a text block
            else:
                state = State.IN_BLOCK
                buffer.append(line)

        # processing while in text block
        elif state is State.IN_BLOCK:
            # strip right to prevent shenanigans with trailing whitespaces
            line = line.rstrip()

            # '---*' ends the text block and immediately starts a new one
            if line.startswith('---*'):
                yield flush_buffer(curr_name)
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('---*').strip()):
                    curr_name = char_name

            # '---' ends the text block and puts the state in pending
            elif line.startswith('---'):
                yield flush_buffer(curr_name)
                state = State.PENDING
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('---').strip()):
                    curr_name = char_name

            # '===' ends the current chapter and starts a new one
            elif (line.startswith('===')):
                # reset everything before moving on
                yield flush_buffer(curr_name)
                state = State.PENDING
                yield ChapterLine(line.removeprefix('===').strip())

            # everything else gets parsed as text in the text block
            else:
                buffer.append(line)

    # handle any unterminated text blocks at end
    if len(buffer) > 0:
        yield flush_buffer(curr_name)


#
# Line parse directives
#

@dataclass
class Directive:
    '''Abstract base class for Directive lines
    '''

    def apply(self, line: BioTextBlock) -> None: ...


def parse_directive(line: str) -> Directive | None:
    match line.split(None, 1):
        case ['dur', args]: return Dur.parseArgs(args.strip())
        case ['define', args]: Define.parseArgs(args.strip())
        case _: raise LineParseError(f'Unrecognized directive: {line}')


@dataclass
class Dur(Directive):
    ''' Affects the duration of the next BioTextBlock.

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

    def apply(self, line: BioTextBlock) -> None:
        new_duration: Frame = None
        match self.operation:
            case '=': new_duration = self.value
            case '+': new_duration = line.duration + self.value
            case '-': new_duration = line.duration - self.value

        if new_duration <= 0:
            raise DialogueGenException(
                f'Bio block will have negative duration after applying {self}: {line}')

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
