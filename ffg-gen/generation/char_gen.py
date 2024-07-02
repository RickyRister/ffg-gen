from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from enum import Enum
from collections.abc import Generator
from mlt_fix import fix_mlt
from filters import affineFilterArgs, brightnessFilterArgs, fadeFilterArgs
from dialogueline import DialogueLine, CharacterInfo
from sysline import SysLine, SetExpr
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


def generate(lines: list[DialogueLine | SysLine], name: str) -> Element:
    """Processes the list of lines into a completed mlt for the given character
    """
    # double check that the character is actually in the scene
    names: set[str] = {line.character.name for line in lines if isinstance(line, DialogueLine)}
    if name not in names:
        raise ValueError(f'{name} does not appear in the dialogue')

    composition = Composition(
        list(processLines(lines, name)),
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)

    xml: str = composition.xml()
    fixedXml: Element = fix_mlt(XML(xml))

    return fixedXml


def processLines(lines: list[DialogueLine | SysLine], name: str) -> Generator[Clip]:
    """Returns a generator that returns a stream of Clips
    """

    charInfo = CharacterInfo.ofName(name)

    # Initialize state to offstage
    state: State = State.OFFSTAGE
    curr_expression: str = charInfo.defaultExpression

    for line in lines:
        # process possible SysLine
        if isinstance(line, SysLine):
            if isinstance(line, SetExpr) and line.name == name:
                curr_expression = line.expression
            continue

        # otherwise we're processing a DialogueLine
        speaker: str = line.character.name

        if speaker == name:
            curr_expression = line.expression

        match(state):
            case State.OFFSTAGE:
                if (speaker == name):
                    state = State.FRONT
                    yield create_clip(Transition.FULL_ENTER, charInfo, curr_expression, line.duration)
                else:
                    state = State.BACK
                    yield create_clip(Transition.HALF_ENTER, charInfo, curr_expression, line.duration)
            case State.BACK:
                if (speaker == name):
                    state = State.FRONT
                    yield create_clip(Transition.IN, charInfo, curr_expression, line.duration)
                else:
                    state = State.BACK
                    yield create_clip(Transition.STAY_OUT, charInfo, curr_expression, line.duration)
            case State.FRONT:
                if (speaker == name):
                    state = State.FRONT
                    yield create_clip(Transition.STAY_IN, charInfo, curr_expression, line.duration)
                else:
                    state = State.BACK
                    yield create_clip(Transition.OUT, charInfo, curr_expression, line.duration)

    # final exit
    match(state):
        case State.FRONT: yield create_clip(Transition.FULL_EXIT, charInfo, curr_expression, configs.MOVEMENT.exitDuration)
        case State.BACK: yield create_clip(Transition.HALF_EXIT, charInfo, curr_expression, configs.MOVEMENT.exitDuration)


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

    # apply fade in if required
    if transition in (Transition.FULL_ENTER, Transition.HALF_ENTER):
        clip.fx('brightness', fadeFilterArgs(f'00:00:00.000=0;{configs.MOVEMENT.fadeInEnd}=1'))

    # apply fade out if required
    if transition in (Transition.FULL_EXIT, Transition.HALF_EXIT):
        clip.fx('brightness', fadeFilterArgs(f'00:00:00.000=1;{configs.MOVEMENT.fadeOutEnd}=0'))

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
