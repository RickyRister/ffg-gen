'''Custom exceptions used in this project
'''


class DialogueGenException(Exception):
    '''Parent exception class of expected exceptions that are raised when generating dialogue.

    This exception should signal that something is wrong with the input file or configs.
    '''


class MissingInfoError(DialogueGenException):
    '''A certain Info property is required right now, but is missing.
    '''

    def __init__(self, property_name: str, char_name: str = None):
        self.property_name = property_name
        self.char_name = char_name

    def __str__(self) -> str:
        if self.char_name is not None:
            return f"Could not resolve '{self.property_name}' property for {self.char_name}"
        else:
            return f"Could not resolve '{self.property_name}' property"


class MissingConfigError(DialogueGenException):
    '''A property (other than an Info property) is being referenced right now, but is missing from the configs.
    '''


class NonExistentPropertyError(DialogueGenException):
    '''You're trying to reference a non-existent property.
    '''

class LineParseError(Exception):
    '''Invalid line
    '''

class CliError(Exception):
    '''Invalid command line args
    '''