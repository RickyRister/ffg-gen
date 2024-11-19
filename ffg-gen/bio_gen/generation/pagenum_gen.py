from typing import Generator
from dataclasses import dataclass
from vidpy import Clip
from vidpy.utils import Frame
import filters
from geometry import Geometry
from lines import Line, SysLine
from bio_gen.bioinfo import BioInfo
from bio_gen.bioline import BioTextBlock
from configcontext import ConfigContext
from vidpy_extension.ext_composition import ExtComposition
import configs


# === Objects ====

@dataclass
class ClipInfo:
    '''An intermediate representation that stores each processed line before it gets turned into clips.
    Doing two passes helps determine which clips are on the ends
    '''
    bioInfo: BioInfo
    pagenum: int
    duration: Frame
    is_first: bool = False  # these fields will be modified after creation
    is_last: bool = False


# === Entrance ====

def generate(lines: list[Line]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    # generate clip infos
    clip_infos = list(process_lines(lines))

    # mark the ends
    clip_infos[0].is_first = True
    clip_infos[-1].is_last = True

    # convert to clips
    clips = [to_clip(clip_info, len(clip_infos)) for clip_info in clip_infos]

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


# === Processing Lines ===

def process_lines(lines: list[Line]) -> Generator[ClipInfo, None, None]:
    context = ConfigContext(BioInfo)

    for line in lines:
        if isinstance(line, SysLine):
            # always run the pre_hook first if it's a sysline
            line.pre_hook(context)

        elif isinstance(line, BioTextBlock):
            # create the clip info
            bioInfo = context.get_char(line.name)
            yield ClipInfo(bioInfo, line.pagenum, line.duration)


def to_clip(clip_info: ClipInfo, page_count: int) -> Clip:
    bioInfo = clip_info.bioInfo

    # create base clip
    clip: Clip = Clip('color:#00000000', start=Frame(0)).set_duration(clip_info.duration)

    text_filter_args = filters.textFilterArgs(
        text=f'{clip_info.pagenum}/{page_count}',
        geometry=bioInfo.pagenumGeometry,
        font=bioInfo.pagenumFont,
        size=bioInfo.pagenumFontSize,
        weight=bioInfo.pagenumWeight,
        color=bioInfo.pagenumFillColor,
        olcolor=bioInfo.pagenumOutlineColor,
        halign='right',
        valign='bottom'
    )

    # apply bottom text layer
    clip.fx('dynamictext', text_filter_args)

    # apply crop for bottom text layer
    clip.fx('qtcrop', filters.cropFilterArgs(
        rect=Geometry(0, 0, bioInfo.pagenumCropX, configs.VIDEO_MODE.height)
    ))

    # apply inbetween fade filters if required
    if not clip_info.is_first:
        fade_end = bioInfo.textFadeInDur
        clip.fx('brightness', filters.opacityFilterArgs(f'0=0;{fade_end}=1'))

    if not clip_info.is_last:
        fade_start = clip_info.duration - bioInfo.textFadeOutDur
        clip.fx('brightness', filters.opacityFilterArgs(f'{fade_start}=1;{clip_info.duration}=0'))

    # apply second text layer
    text_filter_args = text_filter_args.copy()
    text_filter_args['argument'] = f'/{page_count}'

    clip.fx('dynamictext', text_filter_args)

    # apply boundary fade filters if required
    if clip_info.is_first:
        fade_end = bioInfo.firstFadeInDur
        clip.fx('brightness', filters.opacityFilterArgs(f'0=0;{fade_end}=1'))

    if clip_info.is_last:
        fade_start = clip_info.duration - bioInfo.lastFadeOutDur
        clip.fx('brightness', filters.opacityFilterArgs(f'{fade_start}=1;{clip_info.duration}=0'))

    # and we're done!
    return clip
