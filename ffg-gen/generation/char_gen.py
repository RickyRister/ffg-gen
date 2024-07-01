from functools import partial
from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from enum import Enum
from mlt_fix import fix_mlt
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogueline import DialogueLine, CharacterInfo
import configs

State = Enum('State', ['OFFSTAGE', 'FRONT', 'BACK'])


class Transition(Enum):
    IN = 1
    OUT = 2
    FULL_ENTER = 3
    HALF_ENTER = 4
    FULL_EXIT = 5
    HALF_EXIT = 6
    STAY_IN = 7
    STAY_OUT = 8


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

    clips: list[Clip] = []

    # Initialize state to offstage
    state: State = State.OFFSTAGE

    for dialogueLine in dialogueLines:
        speaker: str = dialogueLine.character.name

        match(state):
            case State.OFFSTAGE:
                if (speaker == name):
                    clips.append(create_clip(dialogueLine, Transition.FULL_ENTER))
                    state = State.FRONT
                else:
                    clips.append(create_clip(dialogueLine, Transition.HALF_ENTER))
                    state = State.BACK
            case State.BACK:
                if (speaker == name):
                    clips.append(create_clip(dialogueLine, Transition.IN))
                    state = State.FRONT
                else:
                    clips.append(create_clip(dialogueLine, Transition.STAY_OUT))
                    state = State.BACK
            case State.FRONT:
                if (speaker == name):
                    clips.append(create_clip(dialogueLine, Transition.STAY_IN))
                    state = State.FRONT
                else:
                    clips.append(create_clip(dialogueLine, Transition.OUT))
                    state = State.BACK

    # final exit
    match(state):
        case State.FRONT: clips.append(create_clip(dialogueLine, Transition.FULL_EXIT))
        case State.BACK: clips.append(create_clip(dialogueLine, Transition.HALF_EXIT))

    return clips    


def create_clip(dialogueLine: DialogueLine, transition: Transition) -> Clip:
    pass
