import dataclasses
from dataclasses import dataclass, field
from typing import Any, Self
from functools import cache
from vidpy.utils import Frame
from geometry import Geometry, Offset
from mlt_resource import MltResource
import infohelper
from exceptions import MissingConfigError
from . import dconfigs


UNSET = infohelper.UNSET


@dataclass(frozen=True)
class CharacterInfo(infohelper.Info):
    """A representation of the info of a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """
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
    geometry: Geometry = field(default_factory=lambda: Geometry(0,0))
    frontOffset: Offset = Offset()
    backOffset: Offset = Offset()
    offstageOffset: Offset = Offset()

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

        infohelper.default_to(self, 'enterEnd', 'moveEnd')

    @classmethod
    @cache
    def of_name(cls, name: str | None) -> Self:
        if name is None:
            return CharacterInfo(**dconfigs.CHAR_INFO.get('common'))

        character_json: dict = merge_down_chain(name)
        return CharacterInfo(name=name, **character_json)


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
