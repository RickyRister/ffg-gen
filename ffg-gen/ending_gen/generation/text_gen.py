from dataclasses import dataclass
from typing import Generator, Iterable
from itertools import zip_longest
from vidpy import Clip
from vidpy.utils import Frame
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from lines import Line, SysLine
from ending_gen.endingline import TextLine, PageTurn, Wait
from ending_gen.endinginfo import EndingInfo
from vidpy_extension.blankclip import BlankClip
from vidpy_extension.ext_composition import ExtComposition
import configs
from configcontext import ConfigContext


# === Objects ====

@dataclass
class LineInfo:
    '''An intermediate representation that stores each processed line,
    to make it easier to process into ClipInfo.
    '''
    text: str | None            # Can be multi-line. None means it's a Wait
    charInfo: EndingInfo        # ending info to use for this line
    duration: Frame             # duration of just this line

    @property
    def name(self) -> str:
        return self.charInfo.name


@dataclass
class ClipInfo:
    '''An intermediate representation that the line after the PageGroup processing,
    before it gets turned into clips
    '''
    text: str                   # Can have leading newlines.
    charInfo: EndingInfo        # ending info to use for this line
    duration: Frame             # duration of this clip
    offset: Frame               # offset from the start of the ClipGroup

    @property
    def name(self) -> str:
        return self.charInfo.name


PageGroup = list[LineInfo]
'''Defines a list of LineInfo that are all part of the same page.
The LineInfo will be in order of appearance.
'''

ClipGroup = list[ClipInfo]
'''Defines a list of ClipInfo that are all part of the same page.
The ClipInfo will be in order of appearance.
'''


# === Entrance ====

def generate(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    """Processes the list of lines into a Composition
    """
    processed_lines: list[PageGroup] = process_lines(lines)

    clip_lists: list[list[Clip]] = process_pagegroups(processed_lines)

    for clips in clip_lists:
        yield ExtComposition(
            clips,
            singletrack=True,
            width=configs.VIDEO_MODE.width,
            height=configs.VIDEO_MODE.height,
            fps=configs.VIDEO_MODE.fps)


# === Processing Lines ===

def process_lines(lines: list[Line]) -> Generator[PageGroup, None, None]:
    '''Returns a generator that that returns ClipInfos,
    with each page grouped into a list, 
    and each group containing the clips in order
    '''
    # Initialize context
    context = ConfigContext(EndingInfo)

    # === start of loop ===

    buffer: list[LineInfo] = list()

    for line in lines:
        # always run the pre_hook first if it's a sysline
        if isinstance(line, SysLine):
            line.pre_hook(context)

        # process depending on line type
        match line:
            # Wait will get added to the buffer as a LineInfo with None text
            case Wait(duration=duration):
                buffer.append(LineInfo(None, context.get_char(None), duration))

            # normal TextLine
            case TextLine(text=text, duration=duration):
                buffer.append(LineInfo(text, context.get_char(None), duration))

            # page turn; yield the current buffer and start a new buffer
            case PageTurn():
                yield buffer
                buffer = list()

            # everything else just gets ignored
            case _: continue

    # finally yield any trailing lines in the buffer
    if len(buffer) > 0:
        yield buffer


# === PageGroups ===

def process_pagegroups(pagegroups: Iterable[PageGroup]) -> list[list[Clip]]:
    '''Processes the PageGroups into clips
    '''
    # process each PageGroup into a ClipGroup
    clipgroups = [flatten_pagegroup(pagegroup) for pagegroup in pagegroups]

    # figure out the maximum number of tracks needed
    num_tracks = max([len(clipgroup) for clipgroup in clipgroups])

    track_list: list[list[Clip]] = [list() for _ in range(num_tracks)]

    for clipgroup in clipgroups:
        # we know track_list is always same or longer than clipgroup,
        # so only clipinfo can be None
        for (clipinfo, track) in zip_longest(clipgroup, track_list, fillvalue=None):
            # fill with blank if the clipgroup doesn't reach this track
            if clipinfo is None:
                track.append(BlankClip.ofDuration(total_duration(clipgroup)))
            else:
                # blank offset
                track.append(BlankClip.ofDuration(clipinfo.offset))

                # actual text portion
                track.append(info_to_clip(clipinfo))

    return track_list


def flatten_pagegroup(pagegroup: PageGroup) -> ClipGroup:
    '''Processes the PageGroup to a ClipGroup, 
    which closer represents the actual info in the Clip.
    '''
    # expand duration to actual durations
    clipgroup: ClipGroup = list()

    curr_offset: Frame = Frame(0)
    curr_newline_count: int = 0

    for lineinfo in pagegroup:
        # increment durations of all existing clips in the group
        for clipinfo in clipgroup:
            # +1 accounts for the 1 frame gap between the previous and current clip
            clipinfo.duration += Frame(1) + lineinfo.duration

        # if the lineinfo is not a Wait...
        if (text := lineinfo.text) is not None:
            # The +1 overshoots since the gap is already covered by being a new clip.
            # But double check to prevent negative offsets.
            offset = curr_offset - Frame(1) if curr_offset != 0 else 0
            
            # add new clip to group
            clipgroup.append(ClipInfo(
                '\n' * curr_newline_count + text,
                lineinfo.charInfo,
                lineinfo.duration,
                offset))  

            # update the newline count
            curr_newline_count += text.count('\n') + 1

        # increment the offset
        # +1 accounts for the 1 frame gap between the previous and current clip
        curr_offset += Frame(1) + lineinfo.duration

    return clipgroup


def total_duration(clipgroup: ClipGroup):
    bottom_clip = clipgroup[0]
    if bottom_clip.offset == 0:
        return bottom_clip.offset + bottom_clip.duration
    else:
        # +1 to account for 1 frame gap between the clips
        return bottom_clip.offset + Frame(1) + bottom_clip.duration


# === Mapping ClipInfo into Clips ===

def info_to_clip(clipinfo: ClipInfo) -> Clip:
    charInfo: EndingInfo = clipinfo.charInfo

    clip = Clip('color:#00000000', start=Frame(0))\
        .set_duration(clipinfo.duration)

    textFilter: dict = textFilterArgs(
        text=clipinfo.text,
        valign='top',
        geometry=charInfo.dialogueGeometry,
        font=charInfo.dialogueFont,
        size=charInfo.dialogueFontSize,
        weight=charInfo.dialogueFontWeight,
        outline=charInfo.dialogueOutlineSize,
        color=charInfo.dialogueFontColor,
        olcolor=charInfo.dialougeOutlineColor)
    
    clip.fx('dynamictext', textFilter)

    # only apply drop text if the duration actually
    if charInfo.dropTextDur > 0:
        dropTextFilter: dict = dropTextFilterArgs(
            resource=charInfo.dropTextMaskPath,
            end=charInfo.dropTextDur)
        
        clip.fx('mask_start', dropTextFilter)

    return clip
