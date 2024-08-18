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
from geometry import Geometry


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
    # save the values here so I don't have to keep calling configs.VIDEO_MODE
    # create base clip
    progbarColor = bioInfo.progbarColor
    clip = Clip(f'color:{progbarColor}', start=Frame(0)).set_duration(line.duration)

    # affine (to turn color fill into strip)
    thickness = bioInfo.progbarThickness
    topY = bioInfo.progbarBaseY

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
    geometry = bioInfo.progbarGeometry
    clip.fx('affine', filters.affineFilterArgs(geometry))

    # fade in
    fadeInEnd = bioInfo.firstFadeInDur if is_first else bioInfo.textFadeInDur
    clip.fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1'))

    # fade out
    fadeOutDur = bioInfo.lastFadeOutDur if is_last else bioInfo.progbarFadeOutDur
    fadeOutStart = line.duration - fadeOutDur
    clip.fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{line.duration}=0'))

    # we're finally done!
    return clip
