from functools import partial
from vidpy import Clip, Composition
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, XML
import re
from mlt_fix import fix_mlt
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogueline import DialogueLine, CharacterInfo
import configs

# This is where most of the heavy lifting happens



def dialogueLineToClip(dialogueLine: DialogueLine) -> Clip:

    characterInfo: CharacterInfo = dialogueLine.character

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
        text=dialogueLine.text,
        geometry=configs.DIALOGUE_BOX.geometry,
        font=configs.DIALOGUE_BOX.font,
        fontSize=configs.DIALOGUE_BOX.fontSize,
        color=characterInfo.color.dialogue)

    return Clip('color:#00000000').set_duration(dialogueLine.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)


def processDialogueLines(dialogueLines: list[DialogueLine]) -> Element:
    clips: list[Clip] = [dialogueLineToClip(line) for line in dialogueLines]
    composition = Composition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)

    xml: str = composition.xml()
    fixedXml: Element = fix_mlt(XML(xml))

    return fixedXml
