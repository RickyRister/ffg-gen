from vidpy import Clip
from vidpy.utils import Frame

import cli_args


class BlankClip(Clip):
    '''A Blank VidPy clip.

    Instances should ONLY be created through the `ofDuration` factory method.

    DO NOT try to create this class using its normal constructor or modify it yourself after creation,
    as it may lead to the duration being incorrectly interpreted as Second instead of Frame.
    '''

    @staticmethod
    def ofDuration(duration: Frame | int) -> Clip:
        '''Creates a blank clip of the given duration.

        Only accepts Frames as duration.
        Will cast the duration to a Frame just to be double sure that it doesn't get interpreted as a Second.

        If the `--fill-blanks` option is on, will instead return a transparent clip with the given duration.
        '''
        if cli_args.ARGS.fill_blanks:
            return Clip('color:#00000000', start=Frame(0)).set_duration(Frame(duration))
        else:
            return BlankClip(start=Frame(0)).set_offset(Frame(duration))

    def args(self, singletrack=False):
        '''Returns melt command line arguments as a list'''

        args = []

        if not singletrack:
            args += ['-track']

        if self.offset > 0:
            args += ['-blank', str(self.offset)]

        return args
