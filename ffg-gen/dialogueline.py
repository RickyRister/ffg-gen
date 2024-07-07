from dataclasses import dataclass
from typing import Iterable
from bisect import bisect
import re
import configs
import sysline
from sysline import SysLine
from characterinfo import CharacterInfo


@dataclass
class DialogueLine:
    """A single parsed line from the script.
    The fields are parsed by using the regex in the config json.
    only the expression field is optional
    """
    name: str
    expression: str | None
    text: str

    @property
    def character(self) -> CharacterInfo:
        """Looks up the CharacterInfo corresponding to this line's character's name
        """
        return CharacterInfo.ofName(self.name)

    @property
    def duration(self) -> float:
        """Determines how long the text should last for depending on its length.
        Returns duration in seconds
        """

        count: int = None
        match configs.DURATIONS.mode:
            case 'char':
                count = len(self.text)
            case 'word':
                count = len(re.findall(r'\w+', self.text))
            case _:
                raise ValueError(f'{configs.DURATIONS.mode} is not a valid durations mode')

        index = bisect(configs.DURATIONS.thresholds, count,
                       key=lambda threshold: threshold.count)
        return configs.DURATIONS.thresholds[index-1].seconds


def parseDialogueFile(lines: Iterable[str]) -> list[DialogueLine | SysLine]:
    """Parse the script into the internal representation
    """
    # parse all lines
    parsed = [parseLine(line) for line in lines]
    # filter out empty lines
    return [line for line in parsed if line is not None]


def parseLine(line: str) -> DialogueLine | SysLine | None:
    """Parse a single line of the file
    """
    # strip before processing
    line = line.strip()

    # skip this line if it's empty or it's a comment
    if (isComment(line)):
        return None

    # process this line as a sysline if it begins with @
    if (line.startswith('@')):
        return sysline.parse_sysline(line[1:])

    text: str = None
    name: str = None
    expression: str = None

    # try to match normal dialogue line
    match = re.match(configs.PARSING.dialogueRegex, line)
    if match:
        expression = match.group('expression').strip()  # normal dialogue line exclusive group
    else:
        # try to match shortened dialogue line and throw if that match also fails
        if not (match := re.match(configs.PARSING.shortDialogueRegex, line)):
            raise ValueError(f'line did not match regex exactly: {line}')

    # groups that appear in both dialogue line types
    name = match.group('name').strip().lower()
    text = match.group('text').strip()

    # process match into a dialogueLine
    return DialogueLine(name, expression, text)


def isComment(line: str) -> bool:
    return len(line) == 0 or line.startswith('#') or line.startswith('//') or line.startswith('(')
