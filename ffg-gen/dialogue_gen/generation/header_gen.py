from vidpy import Clip
from vidpy.utils import Frame
from dialogue_gen.dialogueline import DialogueLine
from dialogue_gen.characterinfo import CharacterInfo
from dialogue_gen.sysline import SysLine, Wait
from vidpy_extension.blankclip import transparent_clip
from vidpy_extension.ext_composition import ExtComposition
import configs
from exceptions import expect
from dialogue_gen.configcontext import ConfigContext


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[DialogueLine | SysLine]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    context = ConfigContext()   # create new context
    clips: list[Clip] = filter_none([lineToClip(line, context) for line in lines])

    return ExtComposition(
        clips,
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)


def lineToClip(line: DialogueLine | SysLine, context: ConfigContext) -> Clip | None:
    if isinstance(line, SysLine):
        # always run the pre_hook first if it's a sysline
        line.pre_hook(context)

        # match sysline
        match line:
            case Wait(duration=duration): return transparent_clip(duration)
            case _: return None

    charInfo: CharacterInfo = context.get_char(line.name)
    overlayPath: str = configs.follow_if_named(
        expect(charInfo.headerOverlayPath, 'headerOverlayPath', charInfo.name))

    return Clip(overlayPath, start=Frame(0)).set_duration(line.duration)
