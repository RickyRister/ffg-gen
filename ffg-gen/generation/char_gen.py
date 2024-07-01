from functools import partial
from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from enum import Enum
from mlt_fix import fix_mlt
from filters import affineFilterArgs, brightnessFilterArgs
from dialogueline import DialogueLine, CharacterInfo
import configs
from configs import CharacterMovementConfigs

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

    charInfo = CharacterInfo.ofName(name)

    # Initialize state to offstage
    state: State = State.OFFSTAGE
    curr_expression: str = charInfo.defaultExpression

    for dialogueLine in dialogueLines:
        speaker: str = dialogueLine.character.name

        if speaker == name:
            curr_expression = dialogueLine.expression

        match(state):
            case State.OFFSTAGE:
                if (speaker == name):
                    clips.append(create_clip(Transition.FULL_ENTER,
                                 charInfo, curr_expression, dialogueLine.duration))
                    state = State.FRONT
                else:
                    clips.append(create_clip(Transition.HALF_ENTER,
                                 charInfo, curr_expression, dialogueLine.duration))
                    state = State.BACK
            case State.BACK:
                if (speaker == name):
                    clips.append(create_clip(Transition.IN,
                                             charInfo, curr_expression, dialogueLine.duration))
                    state = State.FRONT
                else:
                    clips.append(create_clip(Transition.STAY_OUT,
                                 charInfo, curr_expression, dialogueLine.duration))
                    state = State.BACK
            case State.FRONT:
                if (speaker == name):
                    clips.append(create_clip(Transition.STAY_IN,
                                 charInfo, curr_expression, dialogueLine.duration))
                    state = State.FRONT
                else:
                    clips.append(create_clip(Transition.OUT,
                                             charInfo, curr_expression, dialogueLine.duration))
                    state = State.BACK

    # final exit
    match(state):
        case State.FRONT: clips.append(create_clip(Transition.FULL_EXIT, charInfo, curr_expression, configs.MOVEMENT.exitDuration))
        case State.BACK: clips.append(create_clip(Transition.HALF_EXIT, charInfo, curr_expression, configs.MOVEMENT.exitDuration))

    return clips


def create_clip(transition: Transition, charInfo: CharacterInfo, expression: str, duration: float) -> Clip:

    # determine which character config to use
    moveConfigs: CharacterMovementConfigs = configs.PLAYER_MOVEMENT if charInfo.isPlayer else configs.ENEMY_MOVEMENT

    # create clip with portrait
    portraitPath = charInfo.portraitPathFormat.format(expression=expression)
    clip = Clip(portraitPath).set_duration(duration)

    # apply base geometry correction to image if required
    if charInfo.geometry:
        clip.fx('affine', affineFilterArgs(charInfo.geometry))

    # apply movement
    clip.fx('affine', affineFilterArgs(determine_movement_rect(transition, moveConfigs)))

    # apply brightness
    clip.fx('brightness', brightnessFilterArgs(determine_brightness_levels(transition)))

    return clip


def determine_movement_rect(transition: Transition, movementConfigs: CharacterMovementConfigs) -> str:
    moveEnd: str = configs.MOVEMENT.moveEnd
    offstageGeometry: str = movementConfigs.offstageGeometry
    backGeometry: str = movementConfigs.backGeometry

    # calculate frontGeometry if not present
    frontGeometry: str = movementConfigs.frontGeometry
    if not movementConfigs.frontGeometry:
        frontGeometry = f'0 0 {configs.VIDEO_MODE.width} {configs.VIDEO_MODE.height} 1'

    match(transition):
        case Transition.IN:
            return f'00:00:00.000={backGeometry};{moveEnd}={frontGeometry}'
        case Transition.OUT:
            return f'00:00:00.000={frontGeometry};{moveEnd}={backGeometry}'
        case Transition.FULL_ENTER:
            return f'00:00:00.000={offstageGeometry};{moveEnd}={frontGeometry}'
        case Transition.HALF_ENTER:
            return f'00:00:00.000={offstageGeometry};{moveEnd}={backGeometry}'
        case Transition.FULL_EXIT:
            return f'00:00:00.000={frontGeometry};{moveEnd}={offstageGeometry}'
        case Transition.HALF_EXIT:
            return f'00:00:00.000={backGeometry};{moveEnd}={offstageGeometry}'
        case Transition.STAY_IN:
            return frontGeometry
        case Transition.STAY_OUT:
            return backGeometry


def determine_brightness_levels(transition: Transition) -> str:
    fade_end = configs.MOVEMENT.brightnessFadeEnd
    full_level = '1'
    dim_level = configs.MOVEMENT.brightnessFadeLevel

    match(transition):
        case Transition.IN:
            return f'00:00:00.000={dim_level};{fade_end}={full_level}'
        case Transition.OUT:
            return f'00:00:00.000={full_level};{fade_end}={dim_level}'
        case Transition.FULL_ENTER:
            return f'00:00:00.000={dim_level};{fade_end}={full_level}'
        case Transition.HALF_ENTER:
            return f'{dim_level}'
        case Transition.FULL_EXIT:
            return f'00:00:00.000={full_level};{fade_end}={dim_level}'
        case Transition.HALF_EXIT:
            return f'{dim_level}'
        case Transition.STAY_IN:
            return f'{full_level}'
        case Transition.STAY_OUT:
            return f'{dim_level}'
