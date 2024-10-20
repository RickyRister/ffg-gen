from enum import Enum, auto
from typing import Iterable, Generator
from lines import Line
from bio_gen.bioline import BioTextBlock, parse_sysline


class State(Enum):
    PENDING = auto()
    IN_BLOCK = auto()


def parse_bio_file(lines: Iterable[str]) -> list[Line]:
    '''Parse the script into the internal representation.
    The output is given as a list of Lines.

    (We might add chapter support in the future)
    '''
    return list(parse_lines(lines))


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
    '''
    state: State = State.PENDING
    buffer: list[str] = []

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
                yield flush_buffer(curr_name, buffer)
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('---*').strip()):
                    curr_name = char_name

            # '---' ends the text block and puts the state in pending
            elif line.startswith('---'):
                yield flush_buffer(curr_name, buffer)
                state = State.PENDING
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('---').strip()):
                    curr_name = char_name

            # everything else gets parsed as text in the text block
            else:
                buffer.append(line)
    
    # handle any unterminated text blocks at end
    if len(buffer) > 0:
        yield flush_buffer(curr_name, buffer)


def flush_buffer(curr_name: str | None, text_lines: list[str]) -> BioTextBlock:
    '''Joins all the accumulated lines into a text block, then clears the accumlator.
    Strips all trailing blank lines.
    '''
    # keep removing last line if it's blank
    while len(text_lines) > 0 and not text_lines[-1].strip():
        text_lines.pop()

    text: str = str.join('\n', text_lines)
    text_lines.clear()  # clear buffer before returning
    return BioTextBlock(curr_name, text)
