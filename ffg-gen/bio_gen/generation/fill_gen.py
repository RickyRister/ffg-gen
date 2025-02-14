from vidpy import Clip
from vidpy.utils import Frame

import configs
from bio_gen.bioinfo import BioInfo
from filters import opacityFilterArgs
from lines import Line
from mlt_resource import MltResource
from vidpy_extension.ext_composition import ExtComposition


def generate(lines: list[Line], resource: MltResource, do_fade: bool) -> ExtComposition:
    '''Returns a Composition containing a single Clip.
    The lines are used to calculate the duration of the single Clip.
    '''
    # calculate duration
    all_durations: list[Frame] = [line.duration for line in lines if hasattr(line, 'duration')]
    total_duration: Frame = sum(all_durations)

    # the gap between each clip is 1 frame, so we also need to make up those durations
    total_duration += Frame(len(all_durations) - 1)

    # create clip
    clip: Clip = Clip(str(resource), start=Frame(0)).set_duration(total_duration)

    # add fade in and fade out if required
    if do_fade:
        bioInfo: BioInfo = BioInfo.of_common()

        fadeInEnd=bioInfo.firstFadeInDur
        clip.fx('brightness', opacityFilterArgs(f'0=0;{fadeInEnd}=1'))

        fadeOutDur=bioInfo.lastFadeOutDur
        fadeOutStart = total_duration - fadeOutDur
        clip.fx('brightness', opacityFilterArgs(f'{fadeOutStart}=1;{total_duration}=0'))

    return ExtComposition(
        [clip],
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)
