from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from mlt_fix import fix_mlt
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogueline import DialogueLine, CharacterInfo
from sysline import SysLine, Wait
from vidpy_extension.blankclip import BlankClip
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
        match(line):
            case Wait(seconds=seconds): return BlankClip().set_offset(seconds)
            case _: return None

    characterInfo: CharacterInfo = line.character

    headerFilter: dict = textFilterArgs(
        text=characterInfo.displayName,
        geometry=configs.HEADER.geometry,
        size=configs.HEADER.fontSize,
        color=characterInfo.color.headerFill,
        olcolor=characterInfo.color.headerOutline,
        font=configs.HEADER.font)

    dropTextFilter = dropTextFilterArgs(
        resource=configs.DIALOGUE_BOX.dropTextMaskPath,
        end=configs.DIALOGUE_BOX.dropTextEnd)

    richTextFilter = richTextFilterArgs(
        text=line.text,
        geometry=configs.DIALOGUE_BOX.geometry,
        font=configs.DIALOGUE_BOX.font,
        fontSize=configs.DIALOGUE_BOX.fontSize,
        color=characterInfo.color.dialogue)

    return Clip('color:#00000000').set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)
