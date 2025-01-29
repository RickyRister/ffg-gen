from typing import Generator

from vidpy import Clip
from vidpy.utils import Frame

import configs
import filters
from bio_gen.bioinfo import BioInfo
from bio_gen.bioline import BioTextBlock
from configcontext import ConfigContext
from lines import Line, SysLine
from vidpy_extension.ext_composition import ExtComposition


# === Entrance ====

def generate(lines: list[Line]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    clips: list[Clip] = list(process_lines(lines))

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


# === Processing Lines ===

def process_lines(lines: list[Line]) -> Generator[Clip, None, None]:
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
            yield line_to_clip(line, bioInfo, is_first, is_last)


def parse_gain(string: str) -> tuple[float]:
    """
    The textShadowGain property is given as list string of floats, so we have to parse it
    """
    return *(float(value) for value in string.split()),


def line_to_clip(line: BioTextBlock, bioInfo: BioInfo, is_first: bool, is_last: bool) -> Clip:
    clip = Clip('color:#00000000', start=Frame(0)).set_duration(line.duration)

    # delete all occurrences of the line wrap guide
    text: str = line.text.replace(bioInfo.lineWrapGuide, '')

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
    fadeInEnd = bioInfo.firstFadeInDur if is_first else bioInfo.textFadeInDur

    fadeOutDur = bioInfo.lastFadeOutDur if is_last else bioInfo.textFadeOutDur
    fadeOutStart = line.duration - fadeOutDur

    clip.fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1')) \
        .fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{line.duration}=0'))

    return clip
