from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from mlt_fix import fix_mlt
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogueline import DialogueLine
from characterinfo import CharacterInfo
from sysline import SysLine, Wait
from vidpy_extension.blankclip import transparent_clip
import configs


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[DialogueLine | SysLine]) -> Element:
    """Processes the list of lines into a completed mlt for the dialogue
    """
    clips: list[Clip] = filter_none([lineToClip(line) for line in lines])

    composition = Composition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)

    xml: str = composition.xml()
    fixedXml: Element = fix_mlt(XML(xml))

    return fixedXml


def lineToClip(line: DialogueLine | SysLine) -> Clip | None:
    if isinstance(line, SysLine):
        # always run the pre_hook first if it's a sysline
        line.pre_hook()

        # match sysline
        match line:
            case Wait(duration=duration): return transparent_clip(duration)
            case _: return None

    charInfo: CharacterInfo = line.character

    headerFilter: dict = textFilterArgs(
        text=charInfo.displayName,
        geometry=configs.HEADER.geometry,
        font=charInfo.headerFont,
        size=charInfo.headerFontSize,
        color=charInfo.headerFillColor,
        olcolor=charInfo.headerOutlineColor)

    dropTextFilter: dict = dropTextFilterArgs(
        resource=configs.DIALOGUE_BOX.dropTextMaskPath,
        end=configs.DIALOGUE_BOX.dropTextEnd)

    richTextFilter: dict = richTextFilterArgs(
        text=line.text,
        geometry=configs.DIALOGUE_BOX.geometry,
        font=charInfo.dialogueFont,
        fontSize=charInfo.dialogueFontSize,
        color=charInfo.dialogueColor)

    return Clip('color:#00000000').set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)
