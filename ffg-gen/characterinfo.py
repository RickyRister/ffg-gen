from dataclasses import dataclass
from functools import cache
from bisect import bisect
import configs


@dataclass
class CharacterInfo:
    """A representation of the info of a character, read from the config json
    """
    name: str                       # the dict name, for tracking purposes
    displayName: str
    portraitPathFormat: str
    isPlayer: bool
    headerOutlineColor: str
    headerFillColor: str = '#ffffff'
    dialogueColor: str = '#ffffff'
    defaultExpression: str = None   # the default expression the character starts in
    geometry: str = None            # in case the character's base portrait needs to repositioned

    @cache
    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        name = str.lower(name)
        character_json: dict = configs.CHARACTERS.get(name)

        if not character_json:
            raise ValueError(f'{name} not found in characters in config json')

        return CharacterInfo(name=name, **character_json)
