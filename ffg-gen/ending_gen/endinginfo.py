from dataclasses import dataclass
from functools import cache
from typing import Any, Self

from vidpy.utils import Frame

import infohelper
from exceptions import MissingConfigError
from geometry import Geometry
from mlt_resource import MltResource
from . import econfigs

UNSET = infohelper.UNSET


@dataclass(frozen=True)
class EndingInfo(infohelper.Info):
    """A representation of the info for a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """

    # dialogue box configs
    dialogueGeometry: Geometry = UNSET
    dialogueFont: str = UNSET
    dialogueFontSize: int = UNSET
    dialogueFontWeight: int = 500
    dialogueFontColor: str = '#ffffff'
    dialogueOutlineSize: int = 1
    dialougeOutlineColor: int = '#000000'

    dropTextMaskPath: MltResource = UNSET
    dropTextDur: Frame = Frame(0)

    # fade timings
    fadeInDur: Frame = UNSET
    fadeOutDur: Frame = UNSET

    # text fade timings
    textFadeOutDur: Frame = UNSET

    # bg fade timings
    bgFadeInDur: Frame = UNSET
    bgFadeOutDur: Frame = UNSET

    def __post_init__(self):
        infohelper.convert_all_attrs(self)
        infohelper.default_to(self, 'textFadeOutDur', 'fadeOutDur')

    @classmethod
    @cache
    def of_name(cls, name: str | None) -> Self:
        if name is None:
            return EndingInfo(**econfigs.ENDING_INFO.get('common'))

        character_json: dict = merge_down_chain(name)
        return EndingInfo(name=name, **character_json)


# === Config Searching ===

def merge_down_chain(name: str) -> dict[str, Any]:
    '''Starts from the top-level EndingInfo and merges downwards.
    Combines the dicts in the following order, skipping any that isn't present:
    common -> characters.name
    '''
    # grab character json
    character_json: dict | None = econfigs.CHARACTERS.get(name)

    if character_json is None:
        raise MissingConfigError(f'Ending info for {name} not found in config json')

    # grab common json
    common_json: dict = econfigs.ENDING_INFO.get('common')

    # perform merge
    combined_dict: dict = dict()
    if common_json is not None:
        combined_dict |= common_json
    combined_dict |= character_json

    return combined_dict
