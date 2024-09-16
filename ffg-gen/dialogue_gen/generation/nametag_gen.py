from dataclasses import dataclass
from typing import Generator
from vidpy import Clip
from mlt_resource import MltResource
from lines import Line, SysLine
from dialogue_gen.dialogueline import Nametag
from dialogue_gen.characterinfo import CharacterInfo
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
from vidpy_extension.blankclip import transparent_clip
from configcontext import ConfigContext
from filters import affineFilterArgs, brightnessFilterArgs, opacityFilterArgs
import configs


@dataclass
class NametagClipInfo:
    '''Use this to help with merging
    '''
    start_frame: Frame    # The start frame of the clip
    char_info: CharacterInfo  # CharacterInfo to use for the clip


def generate(lines: list[Line]) -> ExtComposition:
    '''Currently, nametag_gen does not handle overlapping nametags well.
    Please DO NOT overlap nametag durations.
    '''
    # find the start frames of the nametag clips
    clip_infos: list[NametagClipInfo] = find_nametag_clips(lines)

    # create clips from info
    # has to be stateful since we need to keep track of time
    clips = list(process_clip_infos(clip_infos))

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def find_nametag_clips(lines: list[Line]) -> Generator[NametagClipInfo, None, None]:
    '''Calculates the start frame and info of each nametag clip.
    '''
    context = ConfigContext(CharacterInfo)
    curr_frame = Frame(0)

    for line in lines:
        if isinstance(line, SysLine):
            # always run the pre_hook first if it's a sysline
            line.pre_hook(context)

            if isinstance(line, Nametag):
                # -1 because the extra frame only applies to blank clips
                yield NametagClipInfo(Frame(curr_frame - 1), context.get_char(line.name))

        if hasattr(line, 'duration'):
            # +1 to account for the 1 frame gap between clips
            curr_frame += line.duration + 1


def process_clip_infos(clip_infos: list[NametagClipInfo]) -> Generator[Clip, None, None]:
    curr_frame = Frame(0)

    for clip_info in clip_infos:
        # add enough blank frames to get from current frame to start of nametag clip
        if clip_info.start_frame > curr_frame:
            yield transparent_clip(clip_info.start_frame - curr_frame)

        # create nametag clip
        yield create_nametag_clip(clip_info.char_info)

        # move current frame to end of nametag clip
        curr_frame = clip_info.start_frame + clip_info.char_info.nametagDur


def create_nametag_clip(char_info: CharacterInfo) -> Clip:
    '''Maps the NametagClipInfo into a Clip
    '''
    # create clip with nametag image
    clip = Clip(str(char_info.nametagPath), start=Frame(0)) \
        .set_duration(char_info.nametagDur)

    in_end = char_info.nametagInDur
    out_start = char_info.nametagDur - char_info.nametagOutDur

    # apply geometry (including movement)
    start_geometry = char_info.nametagGeometry + char_info.nametagInOffset
    end_geometry = char_info.nametagGeometry + char_info.nametagOutOffset
    clip.fx('affine', affineFilterArgs(
        f'0={start_geometry};{in_end}={char_info.nametagGeometry};{out_start}={
            char_info.nametagGeometry};{char_info.nametagDur}={end_geometry}'
    ))

    # apply fade in
    clip.fx('brightness', opacityFilterArgs(f'0=0;{in_end}=1'))

    # apply fade out
    clip.fx('brightness', opacityFilterArgs(f'{out_start}=1;{char_info.nametagDur}=0'))

    return clip
