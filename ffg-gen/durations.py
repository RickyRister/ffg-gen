import math
from dataclasses import dataclass
from vidpy.utils import Frame
import configs
from exceptions import MissingProperty


@dataclass
class Threshold:
    """Contains info about mapping count to duration
    """

    count: int                      # bottom word/char count to hit this threshold
    duration: int | float = None    # duration of clip. int will be intepreted as frames and float as seconds

    def get_duration(self) -> Frame:
        '''Gets the duration, in the unit that's given in the configs
        '''
        if self.duration is None:
            raise MissingProperty(
                f'No duration value configured for threshold at count {self.count}')
        else:
            return to_frame(self.duration)


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
