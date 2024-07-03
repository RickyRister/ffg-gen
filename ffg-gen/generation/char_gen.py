from vidpy import Clip, Composition
from xml.etree.ElementTree import Element, XML
from enum import Enum
from collections.abc import Generator
from mlt_fix import fix_mlt
from filters import affineFilterArgs, brightnessFilterArgs, opacityFilterArgs
from dialogueline import DialogueLine
from characterinfo import CharacterInfo
from sysline import SysLine, SetExpr, Wait, CharEnter, CharExit
import configs
from configs import CharacterMovementConfigs
from vidpy_extension.blankclip import transparent_clip


class State(Enum):
    OFFSCREEN = 0
    FRONT = 1
    BACK = 2
    PENDING_ENTER = 3


class Transition(Enum):
    IN = 1
    OUT = 2
    FULL_ENTER = 3
    HALF_ENTER = 4
    FULL_EXIT = 5
    HALF_EXIT = 6
    STAY_IN = 7
    STAY_OUT = 8
    STAY_OFFSCREEN = 9

    def state_after(transition):
        match(transition):
            case Transition.IN: return State.FRONT
            case Transition.OUT: return State.BACK
            case Transition.FULL_ENTER: return State.FRONT
            case Transition.HALF_ENTER: return State.BACK
            case Transition.FULL_EXIT: return State.OFFSCREEN
            case Transition.HALF_EXIT: return State.OFFSCREEN
            case Transition.STAY_IN: return State.FRONT
            case Transition.STAY_OUT: return State.BACK
            case Transition.STAY_OFFSCREEN: return State.OFFSCREEN


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


def processLines(lines: list[DialogueLine | SysLine], targetName: str) -> Generator[Clip]:
    """Returns a generator that returns a stream of Clips
    """

    charInfo = CharacterInfo.ofName(targetName)

    # Initialize state to offscreen
    curr_state: State = State.OFFSCREEN
    curr_expression: str = charInfo.defaultExpression
    curr_speaker: str = None
    pending_transition: Transition = None

    for line in lines:
        # messy processing depending on line type
        match(line):
            case DialogueLine(character=character, expression=expression):
                # store the new values from the dialogueLine
                curr_speaker = character.name
                if curr_speaker == targetName:
                    curr_expression = expression

            case Wait(duration=duration):
                if curr_speaker is None:
                    # if no one is on screen yet, then we leave a gap
                    yield transparent_clip(duration)
                    continue
                else:
                    # otherwise, we fall through and generate a clip using the previous line's state,
                    # except there is no speaker
                    curr_speaker = None

            case SetExpr(name=name, expression=expression) if name == targetName:
                # set the expression, then continue to next dialogue line
                curr_expression = expression
                continue

            case CharEnter(name=name) if name == targetName:
                # force an enter transition on the next dialogue line
                curr_state = State.PENDING_ENTER
                continue

            case CharExit(name=name) if name == targetName:
                # force an exit transition on the next dialogue line
                match curr_state:
                    case State.FRONT: pending_transition = Transition.FULL_EXIT
                    case State.BACK: pending_transition = Transition.HALF_EXIT
                continue

            case _: continue

        # this part will get run unless continue got called in the match statement
        # make sure whatever line makes it down here has a duration field

        # if no pending transition, then determine transition depending on current conditions
        if pending_transition is None:
            pending_transition = determine_transition(curr_state, curr_speaker == targetName)

        # generate clip using the transition
        yield create_clip(pending_transition, charInfo, curr_expression, line.duration)

        # update state and reset pending transition
        curr_state = Transition.state_after(pending_transition)
        pending_transition = None

    # final exit
    match(curr_state):
        case State.OFFSCREEN: yield transparent_clip(configs.MOVEMENT.exitDuration)
        case State.FRONT: yield create_clip(Transition.FULL_EXIT, charInfo, curr_expression, configs.MOVEMENT.exitDuration)
        case State.BACK: yield create_clip(Transition.HALF_EXIT, charInfo, curr_expression, configs.MOVEMENT.exitDuration)


def determine_transition(curr_state: State, is_speaker: bool) -> Transition:
    """Determines the current transition, given the current State and the current speaker
    """
    match(curr_state, is_speaker):
        case(State.OFFSCREEN, True): return Transition.STAY_OFFSCREEN
        case(State.OFFSCREEN, False): return Transition.STAY_OFFSCREEN
        case(State.PENDING_ENTER, True): return Transition.FULL_ENTER
        case(State.PENDING_ENTER, False): return Transition.HALF_ENTER
        case(State.BACK, True): return Transition.IN
        case(State.BACK, False): return Transition.STAY_OUT
        case(State.FRONT, True): return Transition.STAY_IN
        case(State.FRONT, False): return Transition.OUT


def create_clip(transition: Transition, charInfo: CharacterInfo, expression: str, duration: float) -> Clip:
    # return early if we're still staying offscreen
    if transition is Transition.STAY_OFFSCREEN:
        return transparent_clip(duration)

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
        clip.fx('brightness', opacityFilterArgs(f'00:00:00.000=0;{configs.MOVEMENT.fadeInEnd}=1'))

    # apply fade out if required
    if transition in (Transition.FULL_EXIT, Transition.HALF_EXIT):
        clip.fx('brightness', opacityFilterArgs(f'00:00:00.000=1;{configs.MOVEMENT.fadeOutEnd}=0'))

    return clip


def determine_movement_rect(transition: Transition, movementConfigs: CharacterMovementConfigs) -> str:
    moveEnd: str = configs.MOVEMENT.moveEnd
    offstageGeometry: str = movementConfigs.offstageGeometry
    backGeometry: str = movementConfigs.backGeometry

    # calculate frontGeometry if not present
    frontGeometry: str = movementConfigs.frontGeometry
    if not movementConfigs.frontGeometry:
        frontGeometry = f'0 0 {configs.VIDEO_MODE.width} {configs.VIDEO_MODE.height} 1'

    match transition:
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
