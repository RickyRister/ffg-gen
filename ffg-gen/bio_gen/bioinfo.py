import dataclasses
from dataclasses import dataclass
from typing import Any, Self
from functools import cache
from vidpy.utils import Frame
from exceptions import MissingConfigError
from geometry import Geometry
from mlt_resource import MltResource
import configs
import infohelper
from . import bconfigs

UNSET = infohelper.UNSET


@dataclass(frozen=True)
class BioInfo(infohelper.Info):
    """A representation of the info for a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """

    # bio configs
    bioGeometry: Geometry = UNSET
    bioFont: str = UNSET
    bioFontSize: int = UNSET
    bioFontColor: str = '#ffffff'

    # portrait configs
    portraitPathFormat: MltResource = UNSET
    portraitGeometry: Geometry = UNSET

    # title configs
    titlePathFormat: MltResource = UNSET
    titleGeometry: Geometry = UNSET

    # boundary fade timings
    firstFadeInDur: Frame = UNSET
    lastFadeOutDur: Frame = UNSET

    # text fade timings
    textFadeInDur: Frame = UNSET
    textFadeOutDur: Frame = UNSET

    # progressbar
    progbarColor: str = '#42ffffff'
    progbarBaseY: float = UNSET
    progbarThickness: float = UNSET
    progbarFov: float = UNSET
    progbarAmount: float = 100
    progbarFlip: bool = True
    progbarGeometry: Geometry = UNSET
    progbarFadeOutDur: Frame = UNSET

    # pagenum configs
    pagenumGeometry: Geometry = UNSET
    pagenumFont: str = UNSET
    pagenumFontSize: int = UNSET
    pagenumWeight: int = 500
    pagenumOutlineColor: str = '#000000'
    pagenumFillColor: str = '#ffffff'
    pagenumCropX: float = UNSET

    def __post_init__(self):
        infohelper.convert_all_attrs(self)

        # progress base defaults
        infohelper.default_to_value(self, 'progbarBaseY',
                                    configs.VIDEO_MODE.height/2 - self.progbarThickness/2)

    @classmethod
    @cache
    def of_name(cls, name: str | None) -> Self:
        if name is None:
            return BioInfo(**bconfigs.BIO_INFO.get('common'))
        
        character_json: dict = merge_down_chain(name)
        return BioInfo(name=name, **character_json)


# === Config Searching ===

def merge_down_chain(name: str) -> dict[str, Any]:
    '''Starts from the top-level BioInfo and merges downwards.
    Combines the dicts in the following order, skipping any that isn't present:
    common -> characters.name
    '''
    # grab character json
    character_json: dict | None = bconfigs.CHARACTERS.get(name)

    if character_json is None:
        raise MissingConfigError(f'Bio info for {name} not found in config json')

    # grab common json
    common_json: dict = bconfigs.BIO_INFO.get('common')

    # perform merge
    combined_dict: dict = dict()
    if common_json is not None:
        combined_dict |= common_json
    combined_dict |= character_json

    return combined_dict
