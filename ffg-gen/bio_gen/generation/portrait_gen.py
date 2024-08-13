from enum import Enum
from typing import Generator
from dataclasses import dataclass
from vidpy import Clip
from vidpy.utils import Frame
from filters import affineFilterArgs, opacityFilterArgs
from bio_gen.bioline import Line, BioTextBlock
from bio_gen.bioinfo import BioInfo
from bio_gen.sysline import SysLine, SetExpr
from vidpy_extension.ext_composition import ExtComposition
import configs
from exceptions import expect, DialogueGenException


# === Objects ====

class Transition(Enum):
    IN = 1
    OUT = 2
    BOTH = 3    # we only have this for the edge case when there's a single clip


@dataclass
class ClipInfo:
    '''An intermediate representation that stores each processed line before it gets turned into clips.
    Doing two passes helps determine which clips are on the ends
    '''
    bioInfo: BioInfo
    expression: str
    duration: Frame
    transition: Transition = None   # This field will be mutated after the fact

    def to_clip(self) -> Clip:
        return create_clip(self.bioInfo, self.expression, self.duration, self.transition)


# === Entrance ====

def generate(lines: list[Line], name: str) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    clip_infos: list[ClipInfo] = list(process_lines(lines, name))

    # attach transitions to first and last clip infos
    if len(clip_infos) == 1:
        clip_infos[0] = Transition.BOTH
    elif len(clip_infos) > 1:
        clip_infos[0].transition = Transition.IN
        clip_infos[-1].transition = Transition.OUT

    # map clip infos to clips
    clips = [clip_info.to_clip() for clip_info in clip_infos]

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


# === Processing Lines ===

def process_lines(lines: list[Line], target_name: str) -> Generator[ClipInfo, None, None]:

    curr_expression: str = None

    # === start of loop ===
    for line in lines:
        # always run the pre_hook first if it's a sysline
        if isinstance(line, SysLine):
            line.pre_hook()

        # messy processing depending on line type
        match line:
            # actually do stuff if we get a text
            # (by making it out of the match statement without continuing)
            case BioTextBlock(name=name, text=text):
                ...

            # possible set expression
            case SetExpr(name=name, expression=expression) if name == target_name:
                curr_expression = expression
                continue

            # default case is to do nothing
            case _: continue

        # if we get down here we actually have stuff to create
        yield ClipInfo(BioInfo.of_name(target_name), curr_expression, line.duration)

    # === end of loop ===
    # we don't actually have to do anything lol


def create_clip(bioInfo: BioInfo, expression: str, duration: Frame, transition: Transition) -> Clip:
    # error checking empty expression
    if expression is None:
        raise DialogueGenException(
            f"Character {bioInfo.name} is trying to appear on-screen with undefined expression.")

    # create clip with portrait
    portraitPath = expect(bioInfo.portraitPathFormat, 'portraitPathFormat', bioInfo.name)\
        .format(expression=expression)
    portraitPath = configs.follow_if_named(portraitPath)
    clip = Clip(portraitPath, start=Frame(0)).set_duration(duration)

    # apply base geometry correction to image if required
    if bioInfo.portraitGeometry:
        clip.fx('affine', affineFilterArgs(bioInfo.portraitGeometry))

    # apply fade in if required
    if transition in (Transition.IN, Transition.BOTH):
        fade_end = expect(bioInfo.firstFadeInDur, 'firstFadeInDur', bioInfo.name)
        clip.fx('brightness', opacityFilterArgs(f'0=0;{fade_end}=1'))

    # apply fade out if required
    if transition in (Transition.OUT, Transition.BOTH):
        fade_end = expect(bioInfo.lastFadeOutDur, 'lastFadeOutDur', bioInfo.name)
        clip.fx('brightness', opacityFilterArgs(f'0=1;{fade_end}=0'))

    return clip
