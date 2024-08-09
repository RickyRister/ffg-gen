from dataclasses import dataclass
from vidpy.utils import Second, Frame
import configs
from exceptions import MissingProperty


@dataclass
class DurationFix:
    """Contains info about converting frame durations to timestamp durations.
    The expected out frame won't be known at first.
    We recommend you run the tool first to fill in the expected frame and the correct fix.
    """

    expectedFrames: int     # expected out frame
    fix: str                # timestamp fix
    comment: str = ""       # optional field to leave comment


@dataclass
class Threshold:
    """Contains info about mapping count to duration
    """

    count: int              # bottom word/char count to hit this threshold
    seconds: float = None   # duration of clip in seconds
    frames: int = None      # duration of clip in frames

    def get_duration(self) -> Second | Frame:
        '''Gets the duration, in the unit that's given in the configs
        '''
        match configs.DURATIONS.unit:
            case 'seconds':
                if self.seconds is None:
                    raise MissingProperty(
                        f'No seconds value configured for threshold at count {self.count}')
                else:
                    return Second(self.seconds)
            case 'frames':
                if self.frames is None:
                    raise MissingProperty(
                        f'No frames value configured for threshold at count {self.count}')
                else:
                    return Frame(self.frames)
            case _: raise ValueError(f"'{configs.DURATIONS.unit}' is not a valid duration unit.")
