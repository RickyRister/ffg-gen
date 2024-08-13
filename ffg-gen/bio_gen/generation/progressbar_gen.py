from enum import Enum
from typing import Generator
from vidpy import Clip
from dataclasses import dataclass
from vidpy.utils import Frame
import filters
from bio_gen.bioline import Line, BioTextBlock
from bio_gen.bioinfo import BioInfo
from bio_gen.sysline import SysLine
from bio_gen.configcontext import ConfigContext
from vidpy_extension.ext_composition import ExtComposition
import configs
from geometry import Geometry
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
    context = ConfigContext()

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
    # save the values here so I don't have to keep calling configs.VIDEO_MODE
    # create base clip
    progbarColor = expect(bioInfo.progbarColor, 'progbarColor', bioInfo.name)
    clip = Clip(f'color:{progbarColor}', start=Frame(0)).set_duration(line.duration)

    # affine (to turn color fill into strip)
    thickness = expect(bioInfo.progbarThickness, 'progbarThickness', bioInfo.name)
    topY = expect(bioInfo.progbarBaseY, 'progbarBaseY', bioInfo.name)

    start_rect = Geometry(0, topY, configs.VIDEO_MODE.width, thickness)
    end_rect = Geometry(0, topY, 0, thickness)

    clip.fx('affine', filters.affineFilterArgs(
        f'0={start_rect};{line.duration}={end_rect}', distort=1))

    # frei0r.bigsh0t_eq_to_stereo (to turn strip into circle)
    clip.fx('frei0r.bigsh0t_eq_to_stereo', filters.eqToStereoFilterArgs(
        fov=bioInfo.progbarFov, amount=bioInfo.progbarAmount))

    # flip
    if bioInfo.progbarFlip:
        clip.fx('avfilter.vflip')

    # affine (reposition)
    geometry = expect(bioInfo.progbarGeometry, 'progbarGeometry', bioInfo.name)
    clip.fx('affine', filters.affineFilterArgs(geometry))

    # fade in
    fadeInEnd = expect(bioInfo.firstFadeInDur, 'firstFadeInDur', bioInfo.name) if is_first\
        else expect(bioInfo.textFadeInDur, 'textFadeInDur', bioInfo.name)
    clip.fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1'))

    # fade out
    fadeOutDur = expect(bioInfo.lastFadeOutDur, 'lastFadeOutDur', bioInfo.name) if is_last\
        else expect(bioInfo.progbarFadeOutDur, 'progbarFadeOutDur', bioInfo.name)
    fadeOutStart = line.duration - fadeOutDur
    clip.fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{line.duration}=0'))

    # we're finally done!
    return clip
