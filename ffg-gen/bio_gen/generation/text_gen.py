from dataclasses import dataclass
from typing import Generator

from vidpy import Clip
from vidpy.utils import Frame

import configs
import filters
from bio_gen.bioinfo import BioInfo
from configcontext import ConfigContext
from lines import Line, SysLine
from vidpy_extension.ext_composition import ExtComposition


@dataclass
class ClipInfo:
    """An intermediate representation that stores each processed line before it gets turned into clips.
    """
    text: str
    bioInfo: BioInfo
    duration: Frame
    is_first: bool = False
    is_last: bool = False


# === Entrance ====

def generate(lines: list[Line]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    clip_infos: list[ClipInfo] = list(process_lines(lines))

    clips = [to_clip(clip_info) for clip_info in clip_infos]

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


# === Processing Lines ===

def process_lines(lines: list[Line]) -> Generator[ClipInfo, None, None]:
    context = ConfigContext(BioInfo)

    for index, line in enumerate(lines):
        if isinstance(line, SysLine):
            # always run the pre_hook first if it's a sysline
            line.pre_hook(context)

        else:
            # figure out if the clip is on either boundary
            is_first = True if index == 0 else False
            is_last = True if index == len(lines) - 1 else False

            # create the clip
            bioInfo = context.get_char(line.name)
            yield ClipInfo(line.text, bioInfo, line.duration, is_first, is_last)


def parse_gain(string: str) -> tuple[float]:
    """
    The textShadowGain property is given as list string of floats, so we have to parse it
    """
    return *(float(value) for value in string.split()),


def to_clip(clip_info: ClipInfo) -> Clip:
    clip = Clip('color:#00000000', start=Frame(0)).set_duration(clip_info.duration)

    bioInfo: BioInfo = clip_info.bioInfo

    # delete all occurrences of the line wrap guide
    text: str = clip_info.text.replace(bioInfo.lineWrapGuide, '')

    # possible text shadow
    if bioInfo.textShadowBlur > 0:
        gain: tuple[float] = parse_gain(bioInfo.textShadowGain)
        clip.fx('qtext', filters.richTextFilterArgs(
            text=text,
            geometry=bioInfo.bioGeometry,
            font=bioInfo.bioFont,
            fontSize=bioInfo.bioFontSize,
            align=bioInfo.bioFontAlign)) \
            .fx('avfilter.hue', filters.hueFilterArgs(lightness=bioInfo.textShadowLightness)) \
            .fx('lift_gamma_gain', filters.colorGradingFilterArgs(gain_r=gain[0], gain_g=gain[1], gain_b=gain[2])) \
            .fx('avfilter.gblur', filters.gaussianBlurFilterArgs(bioInfo.textShadowBlur))

    # actual text
    richTextFilter: dict = filters.richTextFilterArgs(
        text=text,
        geometry=bioInfo.bioGeometry,
        font=bioInfo.bioFont,
        fontSize=bioInfo.bioFontSize,
        color=bioInfo.bioFontColor,
        align=bioInfo.bioFontAlign)

    clip.fx('qtext', richTextFilter)

    # figure out fade filters
    fadeInEnd = bioInfo.firstFadeInDur if clip_info.is_first else bioInfo.textFadeInDur

    fadeOutDur = bioInfo.lastFadeOutDur if clip_info.is_last else bioInfo.textFadeOutDur
    fadeOutStart = clip_info.duration - fadeOutDur

    clip.fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1')) \
        .fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{clip_info.duration}=0'))

    return clip
