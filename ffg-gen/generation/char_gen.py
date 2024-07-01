from functools import partial
from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from enum import Enum
from mlt_fix import fix_mlt
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogueline import DialogueLine, CharacterInfo
import configs

State = Enum('State', ['OFFSTAGE', 'FRONT', 'BACK'])


def generate(dialogueLines: list[DialogueLine], name: str) -> Element:
    """Processes the list of DialogueLines into a completed mlt for the given character
    """
    # double check that the character is actually in the scene
    names = set(map(lambda dl: dl.character.name, dialogueLines))
    print(names)
    if name not in names:
        raise ValueError(f'{name} does not appear in the dialogue')

    clips: list[Clip] = processDialogueLines(dialogueLines, name)

    composition = Composition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)

    xml: str = composition.xml()
    fixedXml: Element = fix_mlt(XML(xml))

    return fixedXml


def processDialogueLines(dialogueLines: list[DialogueLine], name: str) -> list[Clip]:

    # Initialize state to offstage
    state: State = State.OFFSTAGE

    for index, dialogueLine in enumerate(dialogueLines, start=1):
        speaker: str = dialogueLine.character.name

        # special processing if last line
        if (index == len(dialogueLines)):
            match(state):
                case State.FRONT: print("front exit")
                case State.BACK: print("back exit")
            break

        match(state):
            case State.OFFSTAGE:
                if (speaker == name):
                    print("front entrance")
                    state = State.FRONT
                else:
                    print("back entrance")
                    state = State.BACK
            case State.BACK:
                if (speaker == name):
                    print("move to front")
                    state = State.FRONT
                else:
                    print("stay back")
                    state = State.BACK
            case State.FRONT:
                if (speaker == name):
                    print("stay front")
                    state = State.FRONT
                else:
                    print("move to back")
                    state = State.BACK

    """
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
        text=dialogueLines.text,
        geometry=configs.DIALOGUE_BOX.geometry,
        font=configs.DIALOGUE_BOX.font,
        fontSize=configs.DIALOGUE_BOX.fontSize,
        color=characterInfo.color.dialogue)

    return Clip('color:#00000000').set_duration(dialogueLines.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)
    """
