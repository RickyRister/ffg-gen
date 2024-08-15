import dataclasses
from dataclasses import dataclass
from typing import Any, Self
from functools import cache
from vidpy.utils import Frame
from exceptions import MissingProperty
from geometry import Geometry
import durations
import configs
import infohelper
from . import bconfigs

UNSET = infohelper.UNSET


@dataclass(frozen=True)
class BioInfo:
    """A representation of the info for a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """

    name: str = None                    # the dict name, for tracking purposes

    # bio configs
    bioGeometry: Geometry = UNSET
    bioFont: str = UNSET
    bioFontSize: int = UNSET
    bioFontColor: str = '#ffffff'

    # portrait configs
    portraitPathFormat: str = UNSET
    portraitGeometry: Geometry = UNSET

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

    def __post_init__(self):
        infohelper.convert_all_attrs(self)

        # progress base defaults
        infohelper.default_to_value(self, 'progbarBaseY',
                                    configs.VIDEO_MODE.height/2 - self.progbarThickness/2)

    def __getattribute__(self, attribute_name: str) -> Any:
        '''Asserts that the value isn't UNSET before returning it.
        Raises a MissingProperty exception otherwise.
        '''
        value = super(BioInfo, self).__getattribute__(attribute_name)
        char_name = super(BioInfo, self).__getattribute__('name')
        infohelper.expect_is_set(value, attribute_name, char_name)
        return value

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
