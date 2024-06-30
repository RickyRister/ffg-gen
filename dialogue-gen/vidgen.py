from functools import partial
from vidpy import Clip, Composition
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, XML
import re
from bisect import bisect
from mlt_fix import makeXmlEditable
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from parsing import DialogueLine, CharacterInfo
import configs

# This is where most of the heavy lifting happens


def determineDuration(text: str) -> float:
    """Determines how long the text should last for depending on its length.
    Returns duration in seconds
    """

    count: int = None
    match(configs.DURATIONS.mode):
        case 'char':
            count = len(text)
        case 'word':
            count = len(re.findall(r'\w+', text))
        case _:
            raise ValueError(f'{configs.DURATIONS.mode} is not a valid durations mode')

    index = bisect(configs.DURATIONS.thresholds, count,
                   key=lambda threshold: threshold.count)
    return configs.DURATIONS.thresholds[index-1].duration


def dialogueLineToClip(dialogueLine: DialogueLine) -> Clip:

    characterInfo: CharacterInfo = dialogueLine.character

    duration: float = determineDuration(dialogueLine.text)

    print(dialogueLine.text, duration)

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

    return Clip('color:#00000000').set_duration(duration)\
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
    fixedXml: Element = makeXmlEditable(XML(xml))

    return fixedXml
