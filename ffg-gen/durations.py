import ast
import math
import re
from bisect import bisect
from dataclasses import dataclass

from vidpy.utils import Frame

import configs


@dataclass
class Threshold:
    '''Contains info about mapping count to duration
    '''
    count: int                      # bottom word/char count to hit this threshold
    duration: Frame

    def __post_init__(self):
        if not isinstance(self.duration, Frame):
            self.duration = to_frame(self.duration)


@dataclass
class Durations:
    '''Holds count mode as well as the count thresholds for each duration
    '''
    mode: str
    thresholds: list[Threshold]     # list of thresholds. Must be in count order

    def __post_init__(self):
        # error checking
        if self.mode not in ('char', 'word'):
            raise ValueError(f'{self.mode} is not a valid durations mode')

        # convert dict to actual objects, if necessary
        if isinstance(self.thresholds[0], dict):
            self.thresholds = [Threshold(**threshold) for threshold in self.thresholds]

    def calc_duration(self, text: str) -> Frame:
        '''Finds the duration of the given text
        '''
        count: int = None
        match self.mode:
            case 'char':
                count = len(text)
            case 'word':
                count = len(re.findall(r'\w+', text))

        index = bisect(self.thresholds, count,
                       key=lambda threshold: threshold.count)
        return self.thresholds[index-1].duration


def to_frame(duration: int | float | str | None) -> Frame:
    '''Converts the duration into a Frame, accounting for the settings

    If duration is an int: interpret as frames. 
    Directly convert to a Frame.

    If duration is a float: interpret as seconds. 
    Multiply the duration by the fps before converting it to a Frame

    If duration is a string: use ast to convert string to either int or float,
    then intepret the value as above.

    Safely passes through any None.
    Frame extends from int, so this function should be idempotent on Frames.
    '''
    # safely pass through None
    if duration is None:
        return None
    
    # parse strings
    if isinstance(duration, str):
        duration = ast.literal_eval(duration)
    
    # interpret numeral
    if isinstance(duration, int):
        return Frame(duration)
    else:
        # we subtract 1 from the resulting frame if it lands on an integer
        return Frame(math.floor(duration * configs.VIDEO_MODE.fps - 0.000001))
