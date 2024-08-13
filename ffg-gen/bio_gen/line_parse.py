from typing import Iterable, Generator
from bio_gen.bioline import Line, BioTextBlock
from bio_gen.sysline import parse_sysline


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
    '''
    in_text_block: bool = False     # tracks if we're in the middle of a text block
    buffer: list[str] = []

    # a character set during a text block start 
    # will persist until another character is set
    curr_name: str = None

    for line in lines:
        # processing while outside text block
        if not in_text_block:
            # strip before processing
            line = line.strip()

            # skip this line if it's empty or it's a comment
            if isComment(line):
                continue

            # process this line as a sysline if it begins with @
            elif (line.startswith('@')):
                yield parse_sysline(line[1:])

            # '--=' starts a text block
            elif (line.startswith('--=')):
                in_text_block = True
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('--=').strip()):
                    curr_name = char_name

            else:
                raise ValueError(f'invalid line?: {line}')

        # processing while in text block
        else:
            # strip right to prevent shenanigans with trailing whitespaces
            line = line.rstrip()

            # '--=' ends a text block
            if line.startswith('--='):
                in_text_block = False
                yield flush_buffer(curr_name, buffer)

            # '---' ends the text block and immediately starts a new one
            elif line.startswith('---'):
                yield flush_buffer(curr_name, buffer)
                # determine if we're also setting a new character
                if (char_name := line.removeprefix('---').strip()):
                    curr_name = char_name

            # everything else gets parsed as text in the text block
            else:
                buffer.append(line)


def flush_buffer(curr_name: str | None, text_lines: list[str]) -> BioTextBlock:
    '''Joins all the accumulated lines into a text block.
    Strips the first leading and last blank lines, if any.
    Also clears the accumulated lines.
    '''
    # remove leading line if it's blank
    if len(text_lines) > 0 and not text_lines[0].strip():
        text_lines.pop(0)

    # remove last line if it's blank
    if len(text_lines) > 0 and not text_lines[-1].strip():
        text_lines.pop()

    text: str = str.join('\n', text_lines)
    text_lines.clear()  # clear buffer before returning
    return BioTextBlock(curr_name, text)
