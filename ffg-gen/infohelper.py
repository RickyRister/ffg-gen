'''Contains helper functions for dealing with the config info dataclasses
'''

from typing import TypeVar, Any, Callable
from vidpy.utils import Frame
from exceptions import MissingInfoError
import durations
from geometry import Geometry
from mlt_resource import MltResource

T = TypeVar("T")
V = TypeVar("V")


# === Sentinel Values

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


# === Conversions during init ===

def convert_all_attrs(obj: Any):
    '''Converts all fields in the obj that are of a type that requires post-init conversation
    '''
    convert_all_of_type(obj, Frame, lambda value: durations.to_frame(value))
    convert_all_of_type(obj, Geometry, lambda value: Geometry.parse(value))
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
