from dataclasses import dataclass
from functools import cache
from typing import Any
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

    # portrait geometry configs
    geometry: str | None = None             # in case the character's base portrait needs to repositioned
    frontGeometry: str = None
    backGeometry: str = None
    offstageGeometry: str = None
    offstageBackGeometry: str = None

    # movement timing configs
    brightnessFadeEnd: str = None
    brightnessFadeLevel: float = None
    moveEnd: str = None
    exitDuration: float = None
    fadeInEnd: str = None
    fadeOutEnd: str = None

    def __post_init__(self):
        '''All unfilled properties will fall through to the global configs
        '''
        # fill all unset fields with the fall-through default
        for attr, value in vars(self).items():
            if value is None:
                setattr(self, attr, self._find_default_value(attr))

    def _find_default_value(self, attr: str) -> Any:
        '''Returns the fall-through default value for the given attr.
        '''
        match attr:
            # exclusive attributes
            # we make them always return themselves, since they should always be set
            case 'name': return self.name
            case 'displayName': return self.displayName
            case 'portraitPathFormat': return self.portraitPathFormat
            case 'isPlayer': return self.isPlayer

            # header configs
            case 'headerFont': return configs.HEADER.font
            case 'headerFontSize': return configs.HEADER.fontSize
            case 'headerOutlineColor': return configs.HEADER.outlineColor
            case 'headerFillColor': return configs.HEADER.fillColor

            # dialogue box configs
            case 'dialogueFont': return configs.DIALOGUE_BOX.font
            case 'dialogueFontSize': return configs.DIALOGUE_BOX.fontSize
            case 'dialogueColor': return configs.DIALOGUE_BOX.fontColor

            # portrait geometry configs
            case 'geometry': return configs.get_char_move(self.isPlayer).geometry
            case 'frontGeometry': return configs.get_char_move(self.isPlayer).frontGeometry
            case 'backGeometry': return configs.get_char_move(self.isPlayer).backGeometry
            case 'offstageGeometry': return configs.get_char_move(self.isPlayer).offstageGeometry
            case 'offstageBackGeometry': return configs.get_char_move(self.isPlayer).offstageBackGeometry

            # movement timing configs
            case 'brightnessFadeEnd': return configs.MOVEMENT.brightnessFadeEnd
            case 'brightnessFadeLevel': return configs.MOVEMENT.brightnessFadeLevel
            case 'moveEnd': return configs.MOVEMENT.moveEnd
            case 'exitDuration': return configs.MOVEMENT.exitDuration
            case 'fadeInEnd': return configs.MOVEMENT.fadeInEnd
            case 'fadeOutEnd': return configs.MOVEMENT.fadeOutEnd

    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that
        """
        name = str.lower(name)
        character_json: dict = configs.CHARACTERS.get(name)

        if not character_json:
            raise ValueError(f'{name} not found in characters in config json')

        return CharacterInfo.get_cached(name)

    @cache
    def get_cached(name: str):
        '''Caches the CharacterInfo by the name.
        This way edits to the CharacterInfo can be remembered.
        Remeber to reset this cache after finishing each component.
        '''
        character_json: dict = configs.CHARACTERS.get(name)
        return CharacterInfo(name=name, **character_json)
