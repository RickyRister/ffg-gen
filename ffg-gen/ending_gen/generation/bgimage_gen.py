from dataclasses import dataclass
from typing import Generator, Iterable
from vidpy import Clip
import filters
import configs
from mlt_resource import MltResource
from lines import Line
from ending_gen.endingline import SetBgImage
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
from vidpy_extension.blankclip import BlankClip
from ending_gen.endinginfo import EndingInfo


@dataclass
class ClipSection:
    '''Use this to help with merging
    '''
    duration: Frame
    image: MltResource


def generate(lines: list[Line]) -> ExtComposition:
    '''Returns a composition possibly containing multiple clips
    '''
    # map to ClipSection
    clip_sections = to_clip_sections(lines)

    # do the merging
    merged_sections = merge_adjacents(clip_sections)

    # map ClipSection to Clips
    clips: list[Clip] = [to_clip(clip_section) for clip_section in merged_sections]

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def to_clip_sections(lines: list[Line]) -> Generator[ClipSection, None, None]:
    '''Maps the Lines to a ClipSection.
    We use a generator since we need to keep track of current image
    '''
    curr_image = None

    for line in lines:
        if isinstance(line, SetBgImage):
            curr_image = line.image

        if hasattr(line, 'duration'):
            yield ClipSection(line.duration, curr_image)


def to_clip(clip_section: ClipSection) -> Clip:
    if (image := clip_section.image) is not None:
        # use common info for now because I can't think of a good way to decide
        # which char info to use
        info = EndingInfo.of_common()

        # figure out fade filters
        fadeInEnd = info.bgFadeInDur
        fadeOutStart = clip_section.duration - info.bgFadeOutDur
        fadeOutEnd = clip_section.duration

        return Clip(str(image), start=Frame(0))\
            .set_duration(clip_section.duration)\
            .fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1'))\
            .fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{fadeOutEnd}=0'))
    else:
        return BlankClip.ofDuration(clip_section.duration)


def merge_adjacents(clip_sections: Iterable[ClipSection]) -> Generator[ClipSection, None, None]:
    '''Processes the list and merges any adjacent ClipSection with the same state into a single ClipSection
    '''
    curr_section: ClipSection = next(clip_sections)  # pop first element
    for section in clip_sections:
        # if state is the same, then merge
        if section.image == curr_section.image:
            # we need to add +1 because the gap between each clip is 1 frame
            new_duration = curr_section.duration + section.duration + Frame(1)
            curr_section = ClipSection(new_duration, section.image)
        else:
            # otherwise pinch off the current section and start tracking the new section
            yield curr_section
            curr_section = section

    # end of loop; yield final unyielded section
    yield curr_section
