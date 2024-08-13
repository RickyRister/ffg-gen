from vidpy import Clip
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
import configs
from exceptions import expect
from filters import opacityFilterArgs
from bio_gen.bioline import Line
from bio_gen.bioinfo import BioInfo


def generate(lines: list[Line], resource: str, do_fade: bool) -> ExtComposition:
    '''Returns a Composition containing a single Clip.
    The lines are used to calculate the duration of the single Clip.
    '''
    # caculate duration
    all_durations: list[Frame] = [line.duration for line in lines if hasattr(line, 'duration')]
    total_duration: Frame = sum(all_durations)

    # the gap between each clip is 1 frame, so we also need to make up those durations
    total_duration += Frame(len(all_durations) - 1)

    # follow resource
    resource = configs.follow_if_named(resource)

    # create clip
    clip: Clip = Clip(resource, start=Frame(0)).set_duration(total_duration)

    # add fade in and fade out if required
    if do_fade:
        bioInfo: BioInfo = BioInfo.of_common()

        fadeInEnd = expect(bioInfo.enterFadeInEnd, 'enterFadeInEnd', bioInfo.name)
        clip.fx('brightness', opacityFilterArgs(f'0=0;{fadeInEnd}=1'))

        fadeOutDur = expect(bioInfo.textFadeOutDur, 'textFadeOutDur')
        fadeOutStart = total_duration - fadeOutDur
        clip.fx('brightness', opacityFilterArgs(f'{fadeOutStart}=1;{total_duration}=0'))

    return ExtComposition(
        [clip],
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)
