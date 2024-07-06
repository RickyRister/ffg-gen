from vidpy import Clip, Composition
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogueline import DialogueLine
from characterinfo import CharacterInfo
from sysline import SysLine, Wait
from vidpy_extension.blankclip import transparent_clip
from vidpy_extension.ext_composition import ExtComposition
import configs
from exceptions import expect


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[DialogueLine | SysLine]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    clips: list[Clip] = filter_none([lineToClip(line) for line in lines])

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def lineToClip(line: DialogueLine | SysLine) -> Clip | None:
    if isinstance(line, SysLine):
        # always run the pre_hook first if it's a sysline
        line.pre_hook()

        # match sysline
        match line:
            case Wait(duration=duration): return transparent_clip(duration)
            case _: return None

    name: str = line.name
    charInfo: CharacterInfo = line.character

    headerFilter: dict = textFilterArgs(
        text=expect(charInfo.displayName, 'displayName', name),
        geometry=configs.HEADER.geometry,
        font=expect(charInfo.headerFont, 'headerFont', name),
        size=expect(charInfo.headerFontSize, 'headerFontSize', name),
        color=expect(charInfo.headerFillColor, 'headerFillColor', name),
        olcolor=expect(charInfo.headerOutlineColor, 'headerOutlineColor', name))

    dropTextFilter: dict = dropTextFilterArgs(
        resource=configs.DIALOGUE_BOX.dropTextMaskPath,
        end=configs.DIALOGUE_BOX.dropTextEnd)

    richTextFilter: dict = richTextFilterArgs(
        text=line.text,
        geometry=configs.DIALOGUE_BOX.geometry,
        font=expect(charInfo.dialogueFont, 'dialogueFont', name),
        fontSize=expect(charInfo.dialogueFontSize, 'dialogueFontSize', name),
        color=expect(charInfo.dialogueColor, 'dialogueColor', name))

    return Clip('color:#00000000').set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)
