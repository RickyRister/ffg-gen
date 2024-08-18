from vidpy import Clip
from vidpy.utils import Frame
from lines import Line, SysLine
from dialogue_gen.dialogueline import Wait
from dialogue_gen.characterinfo import CharacterInfo
from vidpy_extension.blankclip import transparent_clip
from vidpy_extension.ext_composition import ExtComposition
import configs
from mlt_resource import MltResource
from configcontext import ConfigContext


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[Line]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    context = ConfigContext(CharacterInfo)
    clips: list[Clip] = filter_none([lineToClip(line, context) for line in lines])

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def lineToClip(line: Line, context: ConfigContext) -> Clip | None:
    if isinstance(line, SysLine):
        # always run the pre_hook first if it's a sysline
        line.pre_hook(context)

        # match sysline
        match line:
            case Wait(duration=duration): return transparent_clip(duration)
            case _: return None

    charInfo: CharacterInfo = context.get_char(line.name)
    overlayPath: MltResource = charInfo.headerOverlayPath

    return Clip(str(overlayPath), start=Frame(0)).set_duration(line.duration)
