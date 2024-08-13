import dataclasses
from dataclasses import dataclass
from typing import Any, Self
from functools import cache
from vidpy.utils import Frame
from exceptions import MissingProperty
from geometry import Geometry
import durations
import configs
from . import bconfigs


@dataclass(frozen=True)
class BioInfo:
    """A representation of the info for a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """

    name: str = None                    # the dict name, for tracking purposes

    # bio configs
    bioGeometry: Geometry = None
    bioFont: str = None
    bioFontSize: int = None
    bioFontColor: str = '#ffffff'

    # portrait configs
    portraitPathFormat: str = None
    portraitGeometry: Geometry = None

    # boundary fade timings
    firstFadeInDur: Frame = None
    lastFadeOutDur: Frame = None

    # text fade timings
    textFadeInDur: Frame = None
    textFadeOutDur: Frame = None

    # progressbar
    progbarColor: str = '#42ffffff'
    progbarBaseY: float = None
    progbarThickness: float = None
    progbarFov: float = None
    progbarAmount: float = 100
    progbarFlip: bool = True
    progbarGeometry: Geometry = None
    progbarFadeOutDur: Frame = None

    def __post_init__(self):
        # make sure all fields that represent durations are converted to Frame
        duration_attrs = [attr for attr, type in self.__annotations__.items() if type is Frame]
        for duration_attr in duration_attrs:
            if not isinstance((value := getattr(self, duration_attr)), Frame):
                object.__setattr__(self, duration_attr, durations.to_frame(value))

         # make sure all fields that represent geometries are converted to Geometry
        geo_attrs = [attr for attr, type in self.__annotations__.items() if type is Geometry]
        for geo_attr in geo_attrs:
            if not isinstance((value := getattr(self, geo_attr)), Geometry):
                object.__setattr__(self, geo_attr, Geometry.parse(value))

        # progress base defaults
        if self.progbarBaseY is None:
            object.__setattr__(self, 'progbarBaseY',
                               configs.VIDEO_MODE.height/2 - self.progbarThickness/2)

    @cache
    @staticmethod
    def of_common() -> Self:
        '''Returns the singleton instance of top-level BioInfo.
        Will load info from the global config json.
        Make sure the json is loaded in before calling this!
        '''
        return BioInfo(**bconfigs.BIO_INFO.get('common'))

    @cache
    @staticmethod
    def of_name(name: str | None) -> Self:
        '''Looks up the name in the config json and parses the BioInfo from that.
        Caches the result since BioInfo is immutable.
        This will always return the unmodified BioInfo for the given character.

        If None, will just return the common info.

        Note: DOES NOT follow aliases
        '''
        if name is None:
            return BioInfo.of_common()
        character_json: dict = merge_down_chain(name)
        return BioInfo(name=name, **character_json)

    def with_attr(self, attr: str, value: Any) -> Self:
        '''Returns a new instance with the given field changed
        '''
        return dataclasses.replace(self, **{attr: value})

    def with_reset_attr(self, attr: str) -> Self:
        '''Resets the given field to what would've been loaded on startup.
        Checks the characters in the config json, then falls back to the defaults.

        returns: a new instance with the field changed
        '''
        default_value = getattr(BioInfo.of_name(self.name), attr)
        return dataclasses.replace(self, **{attr: default_value})


# === Config Searching ===

def merge_down_chain(name: str) -> dict[str, Any]:
    '''Starts from the top-level BioInfo and merges downwards.
    Combines the dicts in the following order, skipping any that isn't present:
    common -> characters.name
    '''
    # grab character json
    character_json: dict = bconfigs.CHARACTERS.get(name)

    if character_json is None:
        raise MissingProperty(f'Bio info for {name} not found in config json')

    # grab common json
    common_json: dict = bconfigs.BIO_INFO.get('common')

    # perform merge
    combined_dict: dict = dict()
    if common_json is not None:
        combined_dict |= common_json
    combined_dict |= character_json

    return combined_dict
