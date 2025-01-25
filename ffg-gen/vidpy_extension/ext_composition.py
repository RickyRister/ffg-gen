import itertools
import subprocess
from xml.etree.ElementTree import Element, fromstring

from vidpy import Composition, config

import cli_args

'''Code heavily referenced from vidpy
'''


class ExtComposition(Composition):
    '''Extended Composition

    Overrides some of the Composition functionality to specifically suite the needs of this project.
    Much of the code is copied from the superclass's code in vidpy.
    '''

    def single_track_args(self) -> list[str]:
        '''Generate mlt command line arguments for creating only this track.
        Assumes that self.singletrack true.

        Returns:
            list[str]: mlt command line arguments
        '''

        args: list[str] = []

        # add a track for all clips in singletrack
        args += ['-track']

        # add args and transitions for all clips
        for i, clip in enumerate(self.clips):
            clip.track_number = i + 1
            args += clip.args(self.singletrack)
            args += clip.transition_args(i+1)

        # add mask clips
        for i, clip in enumerate(self.clips):
            if clip.mask:
                args += clip.mask.args()

        # add matte transitions for mask clips
        mask_track_number = len(self.clips)
        for i, clip in enumerate(self.clips):
            if clip.mask:
                args += ['-transition', 'matte',
                         'a_track={}'.format(clip.track_number), 'b_track={}'.format(mask_track_number)]
                mask_track_number += 1

        return args

    def xml_as_element(self) -> Element:
        '''Renders the composition as XML and sets the current duration, width, height and fps.

        Returns:
            Element: an mlt xml representation of the composition
        '''

        xml = subprocess.check_output(self.args() + ['-consumer', 'xml'])
        xml = fromstring(xml)

        xml = self.autoset_duration(xml)
        xml = self.set_meta(xml)

        return xml


def compositions_to_mlt(compositions: list[ExtComposition]) -> Element:
    '''Creates a multi-track mlt containing all of the compositions
    '''
    if len(compositions) == 0:
        raise RuntimeError('The generated composition is entirely empty')

    args: list[str] = combine_args(compositions)
    return args_to_xml(args, compositions[0])


def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))


def combine_args(compositions: list[ExtComposition]) -> list[str]:
    '''Combines the single tracks from multiple compositions into the command to generate a single multi-track mlt.

    Returns:
            list[str]: mlt command line arguments
    '''

    args: list[str] = []

    # add the the background track
    args += ['-track', f'color:{cli_args.ARGS.bg_color}', 'out=0']

    # add the combined args for all comps
    args += flatten([composition.single_track_args() for composition in compositions])

    # add composite transitions for all tracks
    for i in range(1, len(compositions) + 1):
        args += ['-transition', 'composite', 'distort=0', 'a_track=0', f'b_track={i}']
        args += ['-transition', 'mix', 'a_track=0', f'b_track={i}']

    return args


def args_to_xml(args: list[str], exemplar: Composition = None) -> Element:
    '''Runs melt on the given command line args to create an mlt file

    Args:
        args: the command line args to melt. DO NOT include the call to melt itself
        exemplar: A Composition to copy the profile/metdata and duration from, in order to fix the mlt
    '''

    xml = subprocess.check_output([config.MELT_BINARY] + args + ['-consumer', 'xml'])
    xml = fromstring(xml)

    if exemplar is not None:
        xml = exemplar.autoset_duration(xml)
        xml = exemplar.set_meta(xml)

    return xml
