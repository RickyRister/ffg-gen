
from vidpy import Clip
from vidpy.utils import Second, Frame
import configs


class BlankClip(Clip):
    '''A Blank VidPy clip.

    Use set_offset() to set the duration of the blank.
    None of the other fields (exception singletrack) matter.

    NOTE: This doesn't actually work because consecutive blank clips will be merged into a single blank clip.
    This throws off the duration fixes.
    Don't use unless you're certain that all gap lengths are covered by duration fixes.
    '''

    def ofDuration(duration: Second | Frame):
        '''Creates a blank clip of the given duration
        '''
        return BlankClip(start=Frame(0)).set_offset(duration)

    def args(self, singletrack=False):
        '''Returns melt command line arguments as a list'''

        args = []

        if not singletrack:
            args += ['-track']

        if self.offset > 0:
            args += ['-blank', str(self.offset)]

        return args


def transparent_clip(duration: Second | Frame) -> Clip:
    '''Creates a blank clip with the given duration.
    If the option --fill-blanks is on, this will instead return a transparent clip with the given duration 
    '''
    if configs.ARGS.fill_blanks:
        return Clip('color:#00000000', start=Frame(0)).set_duration(duration)
    else:
        return BlankClip.ofDuration(duration)
