from dataclasses import dataclass
from functools import cache
from typing import Any
import configs
from movementinfo import MovementInfo


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
            case 'geometry': return MovementInfo.ofIsPlayer(self.isPlayer).geometry
            case 'frontGeometry': return MovementInfo.ofIsPlayer(self.isPlayer).frontGeometry
            case 'backGeometry': return MovementInfo.ofIsPlayer(self.isPlayer).backGeometry
            case 'offstageGeometry': return MovementInfo.ofIsPlayer(self.isPlayer).offstageGeometry
            case 'offstageBackGeometry': return MovementInfo.ofIsPlayer(self.isPlayer).offstageBackGeometry

            # movement timing configs
            case 'brightnessFadeEnd': return MovementInfo.ofIsPlayer(self.isPlayer).brightnessFadeEnd
            case 'brightnessFadeLevel': return MovementInfo.ofIsPlayer(self.isPlayer).brightnessFadeLevel
            case 'moveEnd': return MovementInfo.ofIsPlayer(self.isPlayer).moveEnd
            case 'exitDuration': return MovementInfo.ofIsPlayer(self.isPlayer).exitDuration
            case 'fadeInEnd': return MovementInfo.ofIsPlayer(self.isPlayer).fadeInEnd
            case 'fadeOutEnd': return MovementInfo.ofIsPlayer(self.isPlayer).fadeOutEnd

    def ofName(name: str):
        """Looks up the name in the config json and parses the CharacterInfo from that.
        This method is meant to process any aliases (once we add that) before calling the cached get with the real name
        """
        name = str.lower(name)
        return CharacterInfo.get_cached(name)

    @cache
    def get_cached(name: str):
        '''Looks up the name in the config json and parses the CharacterInfo from that.
        Caches the CharacterInfo by the name.
        This way edits to the CharacterInfo can be remembered.
        Remeber to reset this cache after finishing each component.
        '''
        character_json: dict = configs.CHARACTERS.get(name)

        if not character_json:
            raise ValueError(f'Character info for {name} not found in config json')
        
        return CharacterInfo(name=name, **character_json)

    def reset_attr(self, attr: str):
        '''Resets the given field to what would've been loaded on startup.
        Checks the characters in the config json, then falls back to the defaults
        '''

        # This shouldn't raise exception because we know name already exists in the first dict
        value = configs.CHARACTERS.get(self.name).get(attr)
        if value is None:
            setattr(self, attr, self._find_default_value(attr))
        else:
            setattr(self, attr, value)
