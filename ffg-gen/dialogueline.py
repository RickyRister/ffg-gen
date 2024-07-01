from dataclasses import dataclass
from typing import Iterable
from functools import cache
from bisect import bisect
import re
import configs


@dataclass
class CharacterColor:
    """The colors used for a character's texts
    """
    headerOutline: str
    headerFill: str = "#ffffff"
    dialogue: str = "#ffffff"


@dataclass
class CharacterInfo:
    """A representation of the info of a character, read from the config json
    """
    displayName: str
    portraitPathFormat: str
    color: CharacterColor
    isPlayer: bool
    name: str = None    # the dict name, for tracking purposes
    geometry: str = None    # in case the character's base portrait needs to repositioned

    def __post_init__(self):
        if isinstance(self.color, dict):
            self.color = CharacterColor(**self.color)

    @cache
    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        name = str.lower(name)
        character_json: dict = configs.CHARACTERS.get(name)

        if not character_json:
            raise ValueError(f'{name} not found in characters in config json')

        return CharacterInfo(name=name, **character_json)


@dataclass
class DialogueLine:
    """A single parsed line from the script.
    The fields are parsed by using the regex in the config json.
    only the expression field is optional
    """
    text: str
    character: CharacterInfo
    expression: str | None   

    @property
    def duration(self) -> float:
        """Determines how long the text should last for depending on its length.
        Returns duration in seconds
        """

        count: int = None
        match(configs.DURATIONS.mode):
            case 'char':
                count = len(self.text)
            case 'word':
                count = len(re.findall(r'\w+', self.text))
            case _:
                raise ValueError(
                    f'{configs.DURATIONS.mode} is not a valid durations mode')

        index = bisect(configs.DURATIONS.thresholds, count,
                       key=lambda threshold: threshold.count)
        return configs.DURATIONS.thresholds[index-1].duration


def isComment(line: str) -> bool:
    return len(line) == 0 or line.startswith('#') or line.startswith('//') or line.startswith('(')


def parseDialogueFile(lines: Iterable[str]) -> list[DialogueLine]:
    """Parse the script into the internal representation
    """
    pattern: re.Pattern = re.compile(configs.DIALOGUE_REGEX)

    dialoguelines: list[DialogueLine] = []
    for line in lines:
        # strip before processing
        line = line.strip()

        # skip this line if it's empty or it's a comment
        if (isComment(line)):
            continue

        # match regex and throw if match fails
        match = pattern.match(line)
        if not match or len(match.groups()) != 3:
            raise ValueError(f'line did not match regex exactly: {line}')

        # process match into a dialogueLine
        dialogueline = DialogueLine(
            text=match.group('text').strip(),
            character=CharacterInfo.ofName(match.group('character').strip()),
            expression=int(match.group('expression').strip()))
        dialoguelines.append(dialogueline)

    return dialoguelines
