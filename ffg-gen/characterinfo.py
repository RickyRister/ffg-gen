from dataclasses import dataclass
from typing import Iterable
from functools import cache
from bisect import bisect
import re
import configs
import sysline
from sysline import SysLine


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
    defaultExpression: str  # the default expression the character starts in
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