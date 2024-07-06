from vidpy import Clip
from dialogueline import DialogueLine
from characterinfo import CharacterInfo
from sysline import SysLine, Wait
from vidpy_extension.blankclip import transparent_clip
import configs
from exceptions import expect


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[DialogueLine | SysLine]) -> Composition:
    """Processes the list of lines into a Composition
    """
    clips: list[Clip] = filter_none([lineToClip(line) for line in lines])

    return Composition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def lineToClip(line: DialogueLine | SysLine) -> Clip | None:
    if isinstance(line, SysLine):
        # always run the pre_hook first if it's a sysline
        line.pre_hook()

        # match sysline
        match line:
            case Wait(duration=duration): return transparent_clip(duration)
            case _: return None

    charInfo: CharacterInfo = line.character
    overlayPath: str = expect(charInfo.headerOverlayPath, 'headerOverlayPath', charInfo.name)

    return Clip(overlayPath).set_duration(line.duration)
