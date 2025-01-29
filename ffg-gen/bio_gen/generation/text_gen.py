import dataclasses
from dataclasses import dataclass
from itertools import zip_longest
from typing import Generator, Iterable

from vidpy import Clip
from vidpy.utils import Frame

import configs
import filters
from bio_gen.bioinfo import BioInfo
from configcontext import ConfigContext
from lines import Line, SysLine
from vidpy_extension.blankclip import BlankClip
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
    clip_infos: Iterable[ClipInfo] = process_lines(lines)

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


# ==================
# text split stuff
# ==================

def generate_split(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    """Processes the list of lines into multiple Compositions.
    Each paragraph of the text will be on its own track.
    """
    clip_infos: Iterable[ClipInfo] = process_lines(lines)

    clip_lists: list[list[Clip]] = to_tracks(clip_infos)

    for clips in clip_lists:
        yield ExtComposition(
            clips,
            singletrack=True,
            width=configs.VIDEO_MODE.width,
            height=configs.VIDEO_MODE.height,
            fps=configs.VIDEO_MODE.fps)


def to_tracks(clip_infos: Iterable[ClipInfo]) -> list[list[Clip]]:
    """Maps the list of unsplit ClipInfos into a list of list of Clips, where each inner list represents a track.
    """
    # split each ClipInfo into a list of single-paragraph ClipInfos
    clip_stacks: list[list[ClipInfo]] = [split_clip_info(clip_info) for clip_info in clip_infos]

    # figure out the maximum number of tracks needed
    num_tracks = max([len(clip_stack) for clip_stack in clip_stacks])

    track_list: list[list[Clip]] = [list() for _ in range(num_tracks)]

    for clip_stack in clip_stacks:
        # we know track_list is always same or longer than clip_stack,
        # so only clipinfo can be None
        for (clipinfo, track) in zip_longest(clip_stack, track_list, fillvalue=None):
            # fill with blank if the clip_stack doesn't reach this track
            if clipinfo is None:
                track.append(BlankClip.ofDuration(clip_stack[0].duration))
            else:
                # actual text portion
                track.append(to_clip(clipinfo))

    # the clip stacks are ordered from top to bottom, meaning the first text is on the top of the stack
    # we want it so that the first text is on the bottom of the stack, since that fits how we edit
    track_list.reverse()

    return track_list


def split_clip_info(clip_info: ClipInfo) -> list[ClipInfo]:
    """Splits the single ClipInfo into a separate ClipInfo for each paragraph.
    The new ClipInfos will contain the split text, padded with leading newlines to ensure they all line up.
    The new text will already have the lineWrapGuide symbols removed.
    """
    new_texts: Iterable[str] = split_text(clip_info.text, clip_info.bioInfo.lineWrapGuide)
    return [dataclasses.replace(clip_info, text=new_text) for new_text in new_texts]


def split_text(text_block: str, lineWrapGuide: str) -> Generator[str, None, None]:
    """Splits the entire text block string into individual strings for each paragraph.
    Each resulting string is padded with leading newlines and has the lineWrapGuide symbols removed
    """
    buffer: list[str] = []
    leading_lines = 0  # number of leading lines before the current buffer start

    def flush_buffer() -> Generator[str, None, None]:
        """Flushes the buffer, removing the lineWrapGuide symbols from the text.
        Also updates the leading_lines count
        returns: A generator that might return one or zero strings
        """
        nonlocal leading_lines
        if len(buffer) > 0:
            joined = str.join('\n', buffer)
            yield '\n' * leading_lines + joined.replace(lineWrapGuide, '')

            # update numbers and clean up
            leading_lines += joined.count(lineWrapGuide)
            leading_lines += len(buffer)
            buffer.clear()
        # always increment leading_lines to account for the blank newline
        leading_lines += 1

    for line in text_block.splitlines():
        # strip right to prevent shenanigans with trailing whitespaces
        line = line.rstrip()

        # empty line after rstrip means it's a paragraph break; flush buffer
        if line == '':
            yield from flush_buffer()

        # everything else gets processed as text and added to the buffer
        else:
            buffer.append(line)

    # handle any unterminated text blocks at end
    yield from flush_buffer()
