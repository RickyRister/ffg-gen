from vidpy import Clip
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
import configs
from filters import affineFilterArgs, opacityFilterArgs
from lines import Line
from bio_gen.bioinfo import BioInfo


def generate(lines: list[Line], name: str) -> ExtComposition:
    '''Returns a Composition containing a single Clip.
    The lines are used to calculate the duration of the single Clip.

    This is literally just a tfill that grabs the asset from a BioInfo lol.
    In theory it should care about the currently active character,
    but portrait_gen doesn't do that either, and we haven't gotten multiple character bio scenes yet.

    Currently doesn't support syslines either, but I don't care enough to fix it right now 
    '''
    # caculate duration
    all_durations: list[Frame] = [line.duration for line in lines if hasattr(line, 'duration')]
    total_duration: Frame = sum(all_durations)

    # the gap between each clip is 1 frame, so we also need to make up those durations
    total_duration += Frame(len(all_durations) - 1)

    # add fade in and fade out if required
    bioInfo: BioInfo = BioInfo.of_name(name)

    # create clip
    clip: Clip = Clip(str(bioInfo.titlePathFormat), start=Frame(0)).set_duration(total_duration)

    # apply base geometry correction to image if required
    if bioInfo.titleGeometry:
        clip.fx('affine', affineFilterArgs(bioInfo.titleGeometry))

    # apply fades
    fadeInEnd = bioInfo.firstFadeInDur
    clip.fx('brightness', opacityFilterArgs(f'0=0;{fadeInEnd}=1'))

    fadeOutDur = bioInfo.lastFadeOutDur
    fadeOutStart = total_duration - fadeOutDur
    clip.fx('brightness', opacityFilterArgs(f'{fadeOutStart}=1;{total_duration}=0'))

    return ExtComposition(
        [clip],
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)
