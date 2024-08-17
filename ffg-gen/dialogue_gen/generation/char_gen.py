from vidpy import Clip
from enum import Enum
from typing import Generator, Iterable
from dataclasses import dataclass
from vidpy.utils import Frame
from filters import affineFilterArgs, brightnessFilterArgs, opacityFilterArgs
from dialogue_gen.dialogueline import DialogueLine, Line
from dialogue_gen.characterinfo import CharacterInfo
from dialogue_gen.sysline import SysLine, SetExpr, Wait, CharEnter, CharEnterAll, CharExit, CharExitAll
import configs
import mlt_resource
from configcontext import ConfigContext
from exceptions import DialogueGenException
from vidpy_extension.blankclip import transparent_clip
from vidpy_extension.ext_composition import ExtComposition


# === Objects ====

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
        match transition:
            case Transition.IN: return State.FRONT
            case Transition.OUT: return State.BACK
            case Transition.FULL_ENTER: return State.FRONT
            case Transition.HALF_ENTER: return State.BACK
            case Transition.FULL_EXIT: return State.OFFSCREEN
            case Transition.HALF_EXIT: return State.OFFSCREEN
            case Transition.STAY_IN: return State.FRONT
            case Transition.STAY_OUT: return State.BACK
            case Transition.STAY_OFFSCREEN: return State.OFFSCREEN


@dataclass
class ClipInfo:
    '''An intermediate representation that stores each processed line before it gets turned into clips
    '''
    charInfo: CharacterInfo     # character info at that point
    transition: Transition      # The transition that happens at the start of the clip
    expression: str | None      # label for the portait expression
    duration: Frame    # duration used for the clip
    bring_to_front: bool = False  # whether this clip should bring the character to the front

    @property
    def name(self) -> str:
        return self.charInfo.name

    def to_clip(self) -> Clip:
        return create_clip(self.transition, self.charInfo, self.expression, self.duration)


# === Entrance ====

def generate(lines: list[Line], name: str) -> ExtComposition:
    """Processes the list of lines into a Composition for the given character
    """
    # double check that the character is actually in the scene
    names: set[str] = {configs.follow_global_alias(
        line.name) for line in lines if hasattr(line, 'name')}
    if name not in names:
        raise DialogueGenException(f'{name} does not appear in the dialogue')

    clips = [clip_info.to_clip() for clip_info in processLines(lines, name)]

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def generate_sided(lines: list[Line], names: list[str]) -> Generator[ExtComposition, None, None]:
    """Processes the list of lines into a Composition for the given characters.
    Will make sure that the FRONT character is always on the top layer.
    BACK characters will be sorted by names order.
    """
    # Bounds checking
    if len(names) == 0:
        return
    elif len(names) == 1:
        # if we only have a single character, then it's the same as just generating normally
        yield generate(lines, names[0])
        return

    # process lines and then the track stacks
    processed_lines: list[Generator[ClipInfo]] = [processLines(lines, name) for name in names]
    track_list: list[list[ClipInfo]] = order_clips(processed_lines, names)

    # now convert each track list to a Composition
    for track in track_list:
        clips = [clip_info.to_clip() for clip_info in track]
        yield ExtComposition(
            clips,
            singletrack=True,
            width=configs.VIDEO_MODE.width,
            height=configs.VIDEO_MODE.height,
            fps=configs.VIDEO_MODE.fps)


def order_clips(processed_lines: list[Iterable[ClipInfo]], names: list[str]) -> list[list[ClipInfo]]:
    '''Stacks the clips from the tracks into the right order.
    Make sure the speaker is always in front and the characters don't randomly change order.

    Expects each entry in processed_lines to have the same length.
    Will not check first, so make sure it's correct!
    '''
    # check preconditions
    assert len(processed_lines) == len(names)

    # Each entry in this list represents a track
    # We will be appending clips to the lists in the list
    track_list: list[list[ClipInfo]] = [list() for _ in range(len(names))]

    # We keep a list that tracks the order of the characters
    # Modify this list whenever the character order changes
    curr_name_order: list[str] = names.copy()

    # processing loop
    for clip_stack in zip(*processed_lines):
        # determine if we need to bring anyone to the front
        to_front_name = next((clip.name for clip in clip_stack if clip.bring_to_front), None)
        if to_front_name is not None:
            curr_name_order.pop(curr_name_order.index(to_front_name))
            curr_name_order.insert(0, to_front_name)

        # append the clips to the tracks in the correct order
        for name, track in zip(curr_name_order, track_list):
            track.append(clip_stack[names.index(name)])

    return track_list


# === Processing Lines ===

def processLines(lines: list[Line], targetName: str) -> Generator[ClipInfo, None, None]:
    """Returns a generator that returns a stream of ClipInfo
    """
    # Initialize context
    context = ConfigContext(CharacterInfo)

    # Initialize state to offscreen
    curr_state: State = State.OFFSCREEN
    curr_expression: str = None
    curr_speaker: str = None
    pending_transition: Transition = None

    # === start of loop ===

    for line in lines:
        # always run the pre_hook first if it's a sysline
        if isinstance(line, SysLine):
            line.pre_hook(context)

        # messy processing depending on line type
        match line:
            case DialogueLine(name=name, expression=expression):
                # store the new values from the dialogueLine
                curr_speaker = context.follow_alias(name)
                if curr_speaker == targetName and expression is not None:
                    curr_expression = expression

            case Wait(duration=duration):
                if curr_speaker is None:
                    # if no one is on screen yet, then we leave a gap
                    yield ClipInfo(None, Transition.STAY_OFFSCREEN, curr_expression, duration)
                    continue
                else:
                    # otherwise, we fall through and generate a clip using the previous line's state,
                    # except there is no speaker
                    curr_speaker = None

            case SetExpr(name=name, expression=expression) if context.follow_alias(name) == targetName:
                # set the expression, then continue to next dialogue line
                curr_expression = expression
                continue

            case CharEnter(name=name) if context.follow_alias(name) == targetName:
                # force an enter transition on the next dialogue line
                curr_state = State.PENDING_ENTER
                continue

            case CharEnterAll(is_player=is_player) if (is_player is None) or (is_player == context.get_char(targetName).isPlayer):
                # force an enter transition on the next dialogue line
                curr_state = State.PENDING_ENTER
                continue

            case CharExit(name=name) if context.follow_alias(name) == targetName:
                # force an exit transition on the next dialogue line
                match curr_state:
                    case State.FRONT: pending_transition = Transition.FULL_EXIT
                    case State.BACK: pending_transition = Transition.HALF_EXIT
                continue

            case CharExitAll(is_player=is_player) if (is_player is None) or (is_player == context.get_char(targetName).isPlayer):
                # force an exit transition on the next dialogue line
                match curr_state:
                    case State.FRONT: pending_transition = Transition.FULL_EXIT
                    case State.BACK: pending_transition = Transition.HALF_EXIT
                continue

            case _: continue

        # this part will get run unless continue got called in the match statement
        # make sure whatever line makes it down here has a duration field

        # if no pending transition, then determine transition depending on current conditions
        is_speaker: bool = curr_speaker == targetName
        if pending_transition is None:
            pending_transition = determine_transition(curr_state, is_speaker)

        charInfo: CharacterInfo = context.get_char(targetName, False)

        # generate clip using the transition
        yield ClipInfo(charInfo, pending_transition, curr_expression, line.duration, is_speaker)

        # update state and reset pending transition
        curr_state = Transition.state_after(pending_transition)
        pending_transition = None

    # === end of loop ===

    # grab charInfo again
    charInfo: CharacterInfo = context.get_char(targetName, False)
    exitDuration: Frame = charInfo.exitDuration

    # final exit
    match curr_state:
        case State.FRONT: yield ClipInfo(charInfo, Transition.FULL_EXIT, curr_expression, exitDuration)
        case State.BACK: yield ClipInfo(charInfo, Transition.HALF_EXIT, curr_expression, exitDuration)
        case _: yield ClipInfo(charInfo, Transition.STAY_OFFSCREEN, curr_expression, exitDuration)


def determine_transition(curr_state: State, is_speaker: bool) -> Transition:
    """Determines the current transition, given the current State and the current speaker
    """
    match (curr_state, is_speaker):
        case(State.OFFSCREEN, True): return Transition.STAY_OFFSCREEN
        case(State.OFFSCREEN, False): return Transition.STAY_OFFSCREEN
        case(State.PENDING_ENTER, True): return Transition.FULL_ENTER
        case(State.PENDING_ENTER, False): return Transition.HALF_ENTER
        case(State.BACK, True): return Transition.IN
        case(State.BACK, False): return Transition.STAY_OUT
        case(State.FRONT, True): return Transition.STAY_IN
        case(State.FRONT, False): return Transition.OUT


# === Mapping ClipInfo into Clips ===

def create_clip(transition: Transition, charInfo: CharacterInfo, expression: str, duration: Frame) -> Clip:
    # return early if we're still staying offscreen
    if transition is Transition.STAY_OFFSCREEN:
        return transparent_clip(duration)

    # error checking empty expression
    if expression is None:
        raise DialogueGenException(
            f"Character {charInfo.name} is trying to appear on-screen with undefined expression.")

    # create clip with portrait
    portraitPath = charInfo.portraitPathFormat.format(expression=expression)
    clip = Clip(str(portraitPath), start=Frame(0)).set_duration(duration)

    # apply geometry (including movement)
    clip.fx('affine', affineFilterArgs(determine_movement_rect(transition, charInfo)))

    # apply brightness
    clip.fx('brightness', brightnessFilterArgs(determine_brightness_levels(transition, charInfo)))

    # apply fade in if required
    if transition in (Transition.FULL_ENTER, Transition.HALF_ENTER):
        fade_end = charInfo.fadeInEnd
        clip.fx('brightness', opacityFilterArgs(f'0=0;{fade_end}=1'))

    # apply fade out if required
    if transition in (Transition.FULL_EXIT, Transition.HALF_EXIT):
        fade_end = charInfo.fadeOutEnd
        clip.fx('brightness', opacityFilterArgs(f'0=1;{fade_end}=0'))

    return clip


def determine_movement_rect(transition: Transition, charInfo: CharacterInfo) -> str:
    moveEnd = charInfo.moveEnd
    moveCurve = charInfo.moveCurve
    enterEnd = charInfo.enterEnd

    frontGeometry = charInfo.geometry + charInfo.frontOffset
    backGeometry = charInfo.geometry + charInfo.backOffset
    offstageGeometry = charInfo.geometry + charInfo.offstageOffset
    offstageBackGeometry = charInfo.geometry + charInfo.backOffset + charInfo.offstageOffset

    match transition:
        case Transition.IN:
            return f'0{moveCurve}={backGeometry};{moveEnd}={frontGeometry}'
        case Transition.OUT:
            return f'0{moveCurve}={frontGeometry};{moveEnd}={backGeometry}'
        case Transition.FULL_ENTER:
            return f'0{moveCurve}={offstageGeometry};{enterEnd}={frontGeometry}'
        case Transition.HALF_ENTER:
            return f'0{moveCurve}={offstageBackGeometry};{enterEnd}={backGeometry}'
        case Transition.FULL_EXIT:
            return f'0{moveCurve}={frontGeometry};{moveEnd}={offstageGeometry}'
        case Transition.HALF_EXIT:
            return f'0{moveCurve}={backGeometry};{moveEnd}={offstageBackGeometry}'
        case Transition.STAY_IN:
            return frontGeometry
        case Transition.STAY_OUT:
            return backGeometry


def determine_brightness_levels(transition: Transition, charInfo: CharacterInfo) -> str:
    fade_end = charInfo.brightnessFadeEnd
    full_level = charInfo.frontBrightness
    dim_level = charInfo.backBrightness

    match transition:
        case Transition.IN:
            return f'0={dim_level};{fade_end}={full_level}'
        case Transition.OUT:
            return f'0={full_level};{fade_end}={dim_level}'
        case Transition.FULL_ENTER:
            return f'0={dim_level};{fade_end}={full_level}'
        case Transition.HALF_ENTER:
            return f'{dim_level}'
        case Transition.FULL_EXIT:
            return f'0={full_level};{fade_end}={dim_level}'
        case Transition.HALF_EXIT:
            return f'{dim_level}'
        case Transition.STAY_IN:
            return f'{full_level}'
        case Transition.STAY_OUT:
            return f'{dim_level}'
