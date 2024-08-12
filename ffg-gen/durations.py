import math
from dataclasses import dataclass
from vidpy.utils import Frame
import configs


@dataclass
class Threshold:
    """Contains info about mapping count to duration
    """

    count: int                      # bottom word/char count to hit this threshold
    duration: Frame

    def __post_init__(self):
        if not isinstance(self.duration, Frame):
            self.duration = to_frame(self.duration)


def to_frame(duration: int | float) -> Frame:
    '''Converts the duration into a Frame, accounting for the settings

    If duration is an int: interpret as frames. 
    Directly convert to a Frame.

    If duration is a float: interpret as seconds. 
    Multiply the duration by the fps before converting it to a Frame
    '''
    if isinstance(duration, int):
        return Frame(duration)
    else:
        # we subtract 1 from the resulting frame if it lands on an integer
        return Frame(math.floor(duration * configs.VIDEO_MODE.fps - 0.000001))
