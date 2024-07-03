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
    headerOutlineColor: str = None
    headerFillColor: str = None
    dialogueColor: str = None
    defaultExpression: str = None   # the default expression the character starts in
    geometry: str | None = None            # in case the character's base portrait needs to repositioned
    backGeometry: str = None
    offstageGeometry: str = None
    frontGeometry: str = None

    def __post_init__(self):
        '''All unfilled properties will fall through to the global configs
        '''
        if self.headerOutlineColor is None:
            self.headerOutlineColor = configs.HEADER.outlineColor
        if self.headerFillColor is None:
            self.headerFillColor = configs.HEADER.fillColor
        if self.dialogueColor is None:
            self.dialogueColor = configs.DIALOGUE_BOX.fontColor
        if self.geometry is None:
            self.geometry = configs.MOVEMENT.geometry
        if self.backGeometry is None:
            self.backGeometry = configs.get_char_move(self.isPlayer).backGeometry
        if self.offstageGeometry is None:
            self.offstageGeometry = configs.get_char_move(self.isPlayer).offstageGeometry
        if self.frontGeometry is None:
            self.frontGeometry = configs.get_char_move(self.isPlayer).frontGeometry

    @cache
    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        name = str.lower(name)
        character_json: dict = configs.CHARACTERS.get(name)

        if not character_json:
            raise ValueError(f'{name} not found in characters in config json')

        return CharacterInfo(name=name, **character_json)
