from dataclasses import dataclass
from vidpy.utils import Frame
from . import bconfigs


@dataclass
class Line:
    '''Represents a parsed line from the script.

    Has no functionality on its own.
    Just here so we have a type to group the various line types under 
    to make it easier for type hinting
    '''


@dataclass
class BioTextBlock(Line):
    '''A single parsed text block from the script.
    Note that this can represent multiple actual lines in the script.
    We still treat this thing as a single "line" when processing
    '''
    name: str | None
    text: str
    duration: Frame = None

    def __post_init__(self):
        if self.duration is None:
            self.duration = bconfigs.DURATIONS.calc_duration(self.text)
