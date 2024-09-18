from dataclasses import dataclass
from typing import Generator
from vidpy import Clip
from mlt_resource import MltResource
from lines import Line
from dialogue_gen.dialogueline import Sleep
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
from vidpy_extension.blankclip import BlankClip
import configs


@dataclass
class ClipSection:
    '''Use this to help with merging
    '''
    duration: Frame
    do_show: bool


def generate(lines: list[Line], resource: MltResource) -> ExtComposition:
    '''Returns a composition possibly containing multiple clips
    '''
    # filter lines with duration
    lines_with_duration = [line for line in lines if hasattr(line, 'duration')]

    # map to ClipSection
    clip_sections: list[ClipSection] = [to_clip_section(line) for line in lines_with_duration]

    # do the merging
    merged_sections = merge_adjacents(clip_sections)

    # map ClipSection to Clips
    clips: list[Clip] = [to_clip(clip_section, resource) for clip_section in merged_sections]

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def to_clip_section(line: Line) -> ClipSection:
    '''Maps the Line to a ClipSection.
    expects the Line to have a duration.
    '''
    if isinstance(line, Sleep):
        return ClipSection(line.duration, False)
    else:
        return ClipSection(line.duration, True)


def to_clip(clip_section: ClipSection, resource: MltResource) -> Clip:
    if clip_section.do_show:
        return Clip(str(resource), start=Frame(0)).set_duration(clip_section.duration)
    else:
        return BlankClip.ofDuration(clip_section.duration)


def merge_adjacents(clip_sections: list[ClipSection]) -> Generator[ClipSection, None, None]:
    '''Processes the list and merges any adjacent ClipSection with the same state into a single ClipSection
    '''
    curr_section: ClipSection = clip_sections[0]
    for section in clip_sections[1:]:
        # if state is the same, then merge
        if section.do_show == curr_section.do_show:
            # we need to add +1 because the gap between each clip is 1 frame
            new_duration = curr_section.duration + section.duration + Frame(1)
            curr_section = ClipSection(new_duration, section.do_show)
        else:
            # otherwise pinch off the current section and start tracking the new section
            yield curr_section
            curr_section = section

    # end of loop; yield final unyielded section
    yield curr_section
