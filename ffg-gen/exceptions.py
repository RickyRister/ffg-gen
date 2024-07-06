from typing import TypeVar

T = TypeVar("T")


def expect(value: T, prop_name: str, char_name: str = None) -> T:
    '''Use this to validate that a property is not None before using it.
    Raises an exception if it is None.

    args:
        value: The value to validate
        prop_name: name of the property, for error message purposes
        char_name: character name, if the property belongs to a character
    '''
    if value is not None:
        return value
    elif char_name is not None:
        raise MissingProperty(f'Could not resolve property {prop_name} for character {char_name}')
    else:
        raise MissingProperty(f'Could not resolve property {prop_name}')


class DialogueGenException(Exception):
    '''Parent exception class of expected exceptions that are raised when generating dialogue.

    This exception should signal that something is wrong with the input file or configs.
    '''


class MissingProperty(DialogueGenException):
    '''A certain property is required right now, but is missing.
    '''


class NonExistentProperty(DialogueGenException):
    '''You're trying to reference a non-existent property.
    '''
