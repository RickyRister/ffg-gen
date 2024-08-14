'''Custom exceptions used in this project
'''


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
