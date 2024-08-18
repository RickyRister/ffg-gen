from dataclasses import dataclass
from . import dconfigs
from vidpy.utils import Frame


@dataclass
class Line:
    '''Represents a parsed line from the script.

    Has no functionality on its own.
    Just here so we have a type to group the various line types under 
    to make it easier for type hinting
    '''


@dataclass
class DialogueLine(Line):
    """A single parsed line from the script.
    The fields are parsed by using the regex in the config json.
    only the expression field is optional
    """
    name: str
    expression: str | None
    text: str
    duration: Frame = None

    def __post_init__(self):
        if self.duration is None:
            self.duration = dconfigs.DURATIONS.calc_duration(self.text)
