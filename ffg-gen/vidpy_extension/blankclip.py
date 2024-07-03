
from vidpy import Clip


class BlankClip(Clip):
    '''A Blank VidPy clip.

    Use set_offset() to set the duration of the blank.
    None of the other fields (exception singletrack) matter.

    NOTE: This doesn't actually work because consecutive blank clips will be merged into a single blank clip.
    This throws off the duration fixes.
    Don't use unless you're certain that all gap lengths are covered by duration fixes.
    '''

    def ofDuration(duration: float):
        '''Creates a blank clip of the given duration
        '''
        return BlankClip().set_offset(duration)

    def args(self, singletrack=False):
        '''Returns melt command line arguments as a list'''

        args = []

        if not singletrack:
            args += ['-track']

        if self.offset > 0:
            args += ['-blank', str(self.offset)]

        return args


def transparent_clip(duration: float) -> Clip:
    '''Creates a transparent clip with the given duration.
    This is the best way of having a blank clip without causing durationFix issues
    '''
    return Clip('color:#00000000').set_duration(duration)
