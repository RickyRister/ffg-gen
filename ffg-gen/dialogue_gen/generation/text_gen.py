from vidpy import Clip
from vidpy.utils import Frame
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogue_gen.dialogueline import Line
from dialogue_gen.characterinfo import CharacterInfo
from dialogue_gen.sysline import SysLine, Wait
from vidpy_extension.blankclip import transparent_clip
from vidpy_extension.ext_composition import ExtComposition
import configs
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

    headerFilter: dict = textFilterArgs(
        text=charInfo.displayName,
        geometry=charInfo.headerGeometry,
        font=charInfo.headerFont,
        size=charInfo.headerFontSize,
        color=charInfo.headerFillColor,
        olcolor=charInfo.headerOutlineColor)

    dropTextFilter: dict = dropTextFilterArgs(
        resource=charInfo.dropTextMaskPath,
        end=charInfo.dropTextEnd)

    richTextFilter: dict = richTextFilterArgs(
        text=line.text,
        geometry=charInfo.dialogueGeometry,
        font=charInfo.dialogueFont,
        fontSize=charInfo.dialogueFontSize,
        color=charInfo.dialogueFontColor)

    return Clip('color:#00000000', start=Frame(0)).set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)
