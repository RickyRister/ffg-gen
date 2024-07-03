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

    # header configs
    headerFont: str = None
    headerFontSize: int = None
    headerOutlineColor: str = None
    headerFillColor: str = None

    # dialogue box configs
    dialogueFont: str = None
    dialogueFontSize: int = None
    dialogueColor: str = None

    # movement configs
    defaultExpression: str = None           # the default expression the character starts in
    geometry: str | None = None             # in case the character's base portrait needs to repositioned
    frontGeometry: str = None
    backGeometry: str = None
    offstageGeometry: str = None
    offstageBackGeometry: str = None

    def __post_init__(self):
        '''All unfilled properties will fall through to the global configs
        '''
        # header configs
        if self.headerFont is None:
            self.headerFont = configs.HEADER.font
        if self.headerFontSize is None:
            self.headerFontSize = configs.HEADER.fontSize
        if self.headerOutlineColor is None:
            self.headerOutlineColor = configs.HEADER.outlineColor
        if self.headerFillColor is None:
            self.headerFillColor = configs.HEADER.fillColor

        # dialogue box configs
        if self.dialogueFont is None:
            self.dialogueFont = configs.DIALOGUE_BOX.font
        if self.dialogueFontSize is None:
            self.dialogueFontSize = configs.DIALOGUE_BOX.fontSize
        if self.dialogueColor is None:
            self.dialogueColor = configs.DIALOGUE_BOX.fontColor

        # movement configs
        if self.geometry is None:
            self.geometry = configs.get_char_move(self.isPlayer).geometry
        if self.frontGeometry is None:
            self.frontGeometry = configs.get_char_move(self.isPlayer).frontGeometry
        if self.backGeometry is None:
            self.backGeometry = configs.get_char_move(self.isPlayer).backGeometry
        if self.offstageGeometry is None:
            self.offstageGeometry = configs.get_char_move(self.isPlayer).offstageGeometry
        if self.offstageBackGeometry is None:
            self.offstageBackGeometry = configs.get_char_move(self.isPlayer).offstageBackGeometry

    @cache
    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        name = str.lower(name)
        character_json: dict = configs.CHARACTERS.get(name)

        if not character_json:
            raise ValueError(f'{name} not found in characters in config json')

        return CharacterInfo(name=name, **character_json)
