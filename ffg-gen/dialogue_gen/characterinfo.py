import dataclasses
from dataclasses import dataclass, field
from typing import Any, Self
from functools import cache
from vidpy.utils import Frame
from geometry import Geometry
from mlt_resource import MltResource
import infohelper
from exceptions import MissingConfigError
from . import dconfigs


UNSET = infohelper.UNSET


@dataclass(frozen=True)
class CharacterInfo:
    """A representation of the info of a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """
    name: str = UNSET                       # the dict name, for tracking purposes
    displayName: str = UNSET
    portraitPathFormat: MltResource = UNSET
    isPlayer: bool = UNSET

    # header configs
    headerGeometry: Geometry = UNSET
    headerFont: str = UNSET
    headerFontSize: int = UNSET
    headerWeight: int = 500
    headerOutlineColor: str = UNSET
    headerFillColor: str = '#ffffff'
    headerOverlayPath: MltResource = 'color:#00000000'

    # dialogue box configs
    dialogueGeometry: Geometry = UNSET
    dialogueFont: str = UNSET
    dialogueFontSize: int = UNSET
    dialogueFontColor: str = '#ffffff'
    dropTextMaskPath: MltResource = UNSET
    dropTextEnd: Frame = UNSET

    # portrait geometry configs
    geometry: Geometry = UNSET             # in case the character's base portrait needs to repositioned
    frontGeometry: Geometry = field(      # defaults to no transform
        default_factory=lambda: Geometry(0, 0))
    backGeometry: Geometry = UNSET
    offstageGeometry: Geometry = UNSET
    offstageBackGeometry: Geometry = UNSET

    # brightness configs
    frontBrightness: float = 1
    backBrightness: float = 0.7
    brightnessFadeEnd: Frame = UNSET

    # movement timing configs
    moveEnd: Frame = UNSET
    # https://github.com/mltframework/mlt/blob/master/src/framework/mlt_animation.c#L68
    moveCurve: str = ''
    enterEnd: Frame = UNSET
    exitDuration: Frame = UNSET    # ints will be interpreted as frames and floats as seconds
    fadeInEnd: Frame = UNSET
    fadeOutEnd: Frame = UNSET

    def __post_init__(self):
        infohelper.convert_all_attrs(self)

        infohelper.default_to(self, 'offstageBackGeometry', 'offstageGeometry')
        infohelper.default_to(self, 'enterEnd', 'moveEnd')

    def __getattribute__(self, attribute_name: str) -> Any:
        '''Asserts that the value isn't UNSET before returning it.
        Raises a MissingProperty exception otherwise.
        '''
        value = super(CharacterInfo, self).__getattribute__(attribute_name)
        char_name = super(CharacterInfo, self).__getattribute__('name')
        infohelper.expect_is_set(value, attribute_name, char_name)
        return value

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
    character_json: dict | None = dconfigs.CHARACTERS.get(name)

    if character_json is None:
        raise MissingConfigError(f'Character info for {name} not found in config json')

    # grab player/enemy json
    isPlayer: bool = infohelper.expect_is_set(
        character_json.get('isPlayer'), 'isPlayer', name, None)
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
