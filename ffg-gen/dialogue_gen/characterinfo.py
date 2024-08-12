import dataclasses
from dataclasses import dataclass
from typing import Any, Self
from functools import cache
import configs
from dialogue_gen import dconfigs
from exceptions import MissingProperty, expect


@dataclass(frozen=True)
class CharacterInfo:
    """A representation of the info of a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """
    name: str = None                       # the dict name, for tracking purposes
    displayName: str = None
    portraitPathFormat: str = None
    isPlayer: bool = None

    # header configs
    headerGeometry: str = None
    headerFont: str = None
    headerFontSize: int = None
    headerWeight: int = 500
    headerOutlineColor: str = None
    headerFillColor: str = '#ffffff'
    headerOverlayPath: str = 'color:#00000000'

    # dialogue box configs
    dialogueGeometry: str = None
    dialogueFont: str = None
    dialogueFontSize: int = None
    dialogueFontColor: str = '#ffffff'
    dropTextMaskPath: str = None
    dropTextEnd: str = None

    # portrait geometry configs
    geometry: str | None = None             # in case the character's base portrait needs to repositioned
    frontGeometry: str = None
    backGeometry: str = None
    offstageGeometry: str = None
    offstageBackGeometry: str = None

    # brightness configs
    frontBrightness: float = 1
    backBrightness: float = 0.7
    brightnessFadeEnd: str = None

    # movement timing configs
    moveEnd: str = None
    # https://github.com/mltframework/mlt/blob/master/src/framework/mlt_animation.c#L68
    moveCurve: str = ''
    enterEnd: str = None
    exitDuration: int | float = None    # ints will be interpreted as frames and floats as seconds
    fadeInEnd: str = None
    fadeOutEnd: str = None

    def __post_init__(self):
        # frontGeometry defaults to no transform
        if self.frontGeometry is None:
            object.__setattr__(self, 'frontGeometry',
                               f'0 0 {configs.VIDEO_MODE.width} {configs.VIDEO_MODE.height}')

        # offstageBackGeometry defaults to the same as offstageGeometry
        if self.offstageBackGeometry is None:
            object.__setattr__(self, 'offstageBackGeometry', self.offstageGeometry)

        # enterEnd defaults to same as moveEnd
        if self.enterEnd is None:
            object.__setattr__(self, 'enterEnd', self.moveEnd)

    @cache
    @staticmethod
    def of_common() -> Self:
        '''Returns the singleton instance of top-level CharacterInfo.
        Will load info from the global config json.
        Make sure the json is loaded in before calling this!
        '''
        return CharacterInfo(**dconfigs.CHAR_INFO.get('common'))

    @cache
    @staticmethod
    def of_name(name: str) -> Self:
        '''Looks up the name in the config json and parses the CharacterInfo from that.
        Caches the result since CharacterInfo is immutable.
        This will always return the unmodified CharacterInfo for the given character.

        Note: DOES NOT follow aliases
        '''
        character_json: dict = merge_down_chain(name)
        return CharacterInfo(name=name, **character_json)

    def with_attr(self, attr: str, value: Any) -> Self:
        '''Returns a new instance with the given field changed
        '''
        return dataclasses.replace(self, **{attr: value})

    def with_reset_attr(self, attr: str) -> Self:
        '''Resets the given field to what would've been loaded on startup.
        Checks the characters in the config json, then falls back to the defaults.

        returns: a new instance with the field changed
        '''
        default_value = getattr(CharacterInfo.of_name(self.name), attr)
        return dataclasses.replace(self, **{attr: default_value})


# === Config Searching ===

def merge_down_chain(name: str) -> dict[str, Any]:
    '''Starts from the top-level CharacterInfo and merges downwards.
    Combines the dicts in the following order, skipping any that isn't present:
    common -> player/enemy -> characters.name
    '''
    # grab character json
    character_json: dict = dconfigs.CHARACTERS.get(name)

    if character_json is None:
        raise MissingProperty(f'Character info for {name} not found in config json')

    # grab player/enemy json
    isPlayer: bool = expect(character_json.get('isPlayer'), 'isPlayer', name)
    side: str = 'player' if isPlayer else 'enemy'
    sided_json: dict = dconfigs.CHAR_INFO.get(side)

    # grab common json
    common_json: dict = dconfigs.CHAR_INFO.get('common')

    # perform merge
    combined_dict: dict = dict()
    if common_json is not None:
        combined_dict |= common_json
    if sided_json is not None:
        combined_dict |= sided_json
    combined_dict |= character_json

    return combined_dict
