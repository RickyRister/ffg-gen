from dataclasses import dataclass
from typing import Iterable
from functools import cache
import config


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
    isPlayer: bool = False

    @cache
    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        character_json: dict = config.CONFIG_JSON['characters'][name]
        return CharacterInfo(
            isPlayer=character_json['isPlayer'],
            displayName=character_json['displayName'],
            portraitPathFormat=character_json['portraitPathFormat'],
            color=CharacterColor(
                headerOutline=character_json['color']['headerOutline'],
                headerFill=character_json['color']['headerFill'],
                dialogue=character_json['color']['dialogue']
            ))


@dataclass
class DialogueLine:
    """A single parsed line from the script
    """
    text: str
    character: CharacterInfo
    portraitNum: int


def parseText(lines: Iterable[str]) -> list[DialogueLine]:
    """Parse the script into the internal representation
    """
    pass
