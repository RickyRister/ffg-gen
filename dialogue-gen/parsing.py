from dataclasses import dataclass
from typing import Iterable
from functools import cache
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

    def __post_init__(self):
        if isinstance(self.color, dict):
            self.color = CharacterColor(**self.color)

    @cache
    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        character_json: dict = configs.CHARACTERS.get(str.lower(name))

        if not character_json:
            raise ValueError(f'{name} not found in characters in config json')

        return CharacterInfo(**character_json)


@dataclass
class DialogueLine:
    """A single parsed line from the script.
    The fields are parsed by using the regex in the config json.
    only the num field is optional
    """
    text: str
    character: CharacterInfo
    num: int | None    # the portrait number


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
            num=int(match.group('num').strip()))
        dialoguelines.append(dialogueline)

    return dialoguelines
