from vidpy import Clip
from vidpy.utils import Frame
import filters
from bio_gen.bioline import Line
from bio_gen.bioinfo import BioInfo
from bio_gen.sysline import SysLine
from vidpy_extension.ext_composition import ExtComposition
import configs
import durations
from exceptions import expect


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[Line]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    clips: list[Clip] = filter_none([line_to_clip(line) for line in lines])

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def line_to_clip(line: Line) -> Clip | None:
    if isinstance(line, SysLine):
        # always run the pre_hook first if it's a sysline
        line.pre_hook()

        # match sysline (we currently don't support Wait yet)
        match line:
            case _: return None

    bioInfo: BioInfo = BioInfo.of_common()

    richTextFilter: dict = filters.richTextFilterArgs(
        text=line.text,
        geometry=expect(bioInfo.bioGeometry, 'bioGeometry'),
        font=expect(bioInfo.bioFont, 'bioFont'),
        fontSize=expect(bioInfo.bioFontSize, 'bioFontSize'),
        color=expect(bioInfo.bioFontColor, 'bioFontColor'))

    fadeInEnd = expect(bioInfo.textFadeInEnd, 'textFadeInEnd')
    fadeOutDur = expect(bioInfo.textFadeOutDur, 'textFadeOutDur')
    fadeOutStart = line.duration - fadeOutDur

    return Clip('color:#00000000', start=Frame(0)).set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('brightness', filters.opacityFilterArgs(f'0=0;{fadeInEnd}=1'))\
        .fx('brightness', filters.opacityFilterArgs(f'{fadeOutStart}=1;{line.duration}=0'))
