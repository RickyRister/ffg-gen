from enum import Enum
from typing import Generator
from vidpy import Clip
from dataclasses import dataclass
from vidpy.utils import Frame
import filters
from bio_gen.bioline import Line, BioTextBlock
from bio_gen.bioinfo import BioInfo
from bio_gen.sysline import SysLine
from vidpy_extension.ext_composition import ExtComposition
import configs
from exceptions import expect


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
    for index, line in enumerate(lines):
        if isinstance(line, SysLine):
            # always run the pre_hook first if it's a sysline
            line.pre_hook()

            # match sysline (we currently don't support Wait yet)
            match line:
                case _: ...
        else:
            # figure out if the clip is on either boundary
            is_first = True if index == 0 else False
            is_last = True if index == len(lines) - 1 else False

            # create the clip
            yield line_to_clip(line, is_first, is_last)


def line_to_clip(line: BioTextBlock, is_first: bool, is_last: bool) -> Clip:
    bioInfo: BioInfo = BioInfo.of_name(line.name)

    # text filters
    richTextFilter: dict = filters.richTextFilterArgs(
        text=line.text,
        geometry=expect(bioInfo.bioGeometry, 'bioGeometry'),
        font=expect(bioInfo.bioFont, 'bioFont'),
        fontSize=expect(bioInfo.bioFontSize, 'bioFontSize'),
        color=expect(bioInfo.bioFontColor, 'bioFontColor'))

    # figure out fade filters
    fadeInEnd = expect(bioInfo.enterFadeInEnd, 'enterFadeInEnd') if is_first\
        else expect(bioInfo.textFadeInEnd, 'textFadeInEnd')

    fadeOutDur = expect(bioInfo.exitFadeOutDur, 'exitFadeOutDur') if is_last\
        else expect(bioInfo.textFadeOutDur, 'textFadeOutDur')
    fadeOutStart = line.duration - fadeOutDur

    # create clip
    return Clip('color:#00000000', start=Frame(0)).set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1'))\
        .fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{line.duration}=0'))
