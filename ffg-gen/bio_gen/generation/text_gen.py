from typing import Generator
from vidpy import Clip
from vidpy.utils import Frame
import filters
from lines import Line, SysLine
from bio_gen.bioline import BioTextBlock
from bio_gen.bioinfo import BioInfo
from configcontext import ConfigContext
from vidpy_extension.ext_composition import ExtComposition
import configs


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


def line_to_clip(line: BioTextBlock, bioInfo: BioInfo, is_first: bool, is_last: bool) -> Clip:
    # text filters
    richTextFilter: dict = filters.richTextFilterArgs(
        text=line.text,
        geometry=bioInfo.bioGeometry,
        font=bioInfo.bioFont,
        fontSize=bioInfo.bioFontSize,
        color=bioInfo.bioFontColor)

    # figure out fade filters
    fadeInEnd = bioInfo.firstFadeInDur if is_first else bioInfo.textFadeInDur

    fadeOutDur = bioInfo.lastFadeOutDur if is_last else bioInfo.textFadeOutDur
    fadeOutStart = line.duration - fadeOutDur

    # create clip
    return Clip('color:#00000000', start=Frame(0)).set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1'))\
        .fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{line.duration}=0'))
