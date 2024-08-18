from typing import TypeVar, Any, Callable, Self
from dataclasses import dataclass, replace
from abc import ABC, abstractmethod
from vidpy.utils import Frame
from exceptions import MissingInfoError
import durations
from geometry import Geometry, Offset
from mlt_resource import MltResource

T = TypeVar("T")
V = TypeVar("V")


# ===============
# Sentinel Values
# ===============

class _UNSET_TYPE:
    pass


UNSET = _UNSET_TYPE()
'''Sentinel value to mark an attribute as unset
'''


def expect_is_set(value: T | V, prop_name: str, char_name: str | None = None, sentinel_value: V = UNSET) -> T:
    '''Use this to validate that a property is set before using it.
    Raises an exception if it is not set.

    args:
        value: The value to validate
        prop_name: name of the property, for error message purposes
        char_name: character name, if the property belongs to a character
        sentinel_value: if the value is equal to this value, that means it isn't set
    '''
    if value != sentinel_value:
        return value
    else:
        raise MissingInfoError(prop_name, char_name)


# ===============
# Info base class
# ===============

@dataclass(frozen=True)
class Info(ABC):
    '''This class holds the config info pertaining to the scenario.
    There should be a common info, as well as character-specific info.

    All attributes of Info subclasses should default to UNSET if they don't already have a default.
    The getattribute is overriden to raise a MissingInfoError if trying to access an UNSET attribute.
    This allows config properties to be unset unless required by the component.
    '''
    name: str = None    # The dict name, for tracking purposes

    def __getattribute__(self, attribute_name: str) -> Any:
        '''Asserts that the value isn't UNSET before returning it.
        Raises a MissingProperty exception otherwise.
        '''
        value = super(Info, self).__getattribute__(attribute_name)
        char_name = super(Info, self).__getattribute__('name')
        expect_is_set(value, attribute_name, char_name)
        return value

    @classmethod
    @abstractmethod
    def of_name(cls, name: str | None) -> Self:
        '''Looks up the name in the config json and parses the Info from that.
        Make sure the json is loaded in before calling this!

        If name is None, it will look up the common info.

        This will always return the unmodified Info for the given character.
        Should cache the result since Info is immutable.

        Note: DOES NOT follow aliases
        '''
        ...

    @classmethod
    def of_common(cls) -> Self:
        '''Returns the singleton instance of top-level Info. 
        Shorthand for cls.of_name(None)

        Will load info from the global config json.
        Make sure the json is loaded in before calling this!
        '''
        return cls.of_name(None)


    def with_attr(self, attr: str, value: Any) -> Self:
        '''Returns a new instance with the given field changed
        '''
        return replace(self, **{attr: value})

    def with_reset_attr(self, attr: str) -> Self:
        '''Resets the given field to what would've been loaded on startup.
        Checks the characters in the config json, then falls back to the defaults.

        returns: a new instance with the field changed
        '''
        default_value = getattr(self.__class__.of_name(self.name), attr)
        return replace(self, **{attr: default_value})


# =======================
# Conversions during init
# =======================

def convert_all_attrs(obj: Any):
    '''Converts all fields in the obj that are of a type that requires post-init conversation
    '''
    convert_all_of_type(obj, Frame, lambda value: durations.to_frame(value))
    convert_all_of_type(obj, Geometry, lambda value: Geometry.parse(value))
    convert_all_of_type(obj, Offset, lambda value: Offset.parse(value))
    convert_all_of_type(obj, MltResource, lambda value: MltResource(value))


def convert_all_of_type(obj: Any, target_type: type, mapping_func: Callable):
    attrs = [attr for attr, type in obj.__annotations__.items() if type is target_type]
    for attr in attrs:
        value = object.__getattribute__(obj, attr)
        if value is not UNSET and not isinstance(value, type):
            object.__setattr__(obj, attr, mapping_func(value))


def default_to(obj: Any, target_attr: str, backup_attr: str):
    '''Makes the given attribute default to the value of another attribute
    '''
    value = object.__getattribute__(obj, target_attr)
    if value is UNSET:
        object.__setattr__(obj, target_attr, object.__getattribute__(obj, backup_attr))


def default_to_value(obj: Any, target_attr: str, default_value: Any):
    '''Makes the given attribute default to the given value
    '''
    value = object.__getattribute__(obj, target_attr)
    if value is UNSET:
        object.__setattr__(obj, target_attr, default_value)
