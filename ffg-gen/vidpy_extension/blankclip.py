
from vidpy import Clip

class BlankClip(Clip):
    '''A Blank VidPy clip.

    Use set_offset() to set the duration of the blank.
    None of the other fields (exception singletrack) matter.
    '''

    def args(self, singletrack=False):
        '''Returns melt command line arguments as a list'''

        args = []

        if not singletrack:
            args += ['-track']

        if self.offset > 0:
            args += ['-blank', str(self.offset)]

        return args