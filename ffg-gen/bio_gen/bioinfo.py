import dataclasses
from dataclasses import dataclass
from typing import Any, Self
from functools import cache
from vidpy.utils import Frame
from exceptions import MissingProperty
import durations
from . import bconfigs


@dataclass(frozen=True)
class BioInfo:
    """A representation of the info for a character, read from the config json.
    This class is immutable. Use dataclasses.replace() to modify it
    """

    name: str = None                    # the dict name, for tracking purposes

    # bio configs
    bioGeometry: str = None
    bioFont: str = None
    bioFontSize: int = None
    bioFontColor: str = '#ffffff'

    # portrait configs
    portraitPathFormat: str = None
    portraitGeometry: str = None

    # boundary fade timings
    firstFadeInDur: Frame = None
    lastFadeOutDur: Frame = None
    
    # fade timings
    textFadeInDur: Frame = None
    textFadeOutDur: Frame = None

    def __post_init__(self):
        # make sure all fields that represent durations are converted to Frame
        duration_attrs = [attr for attr, type in self.__annotations__.items() if type is Frame]
        for duration_attr in duration_attrs:
            object.__setattr__(self, duration_attr, durations.to_frame(
                getattr(self, duration_attr)))

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
