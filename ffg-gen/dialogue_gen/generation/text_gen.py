from vidpy import Clip
from vidpy.utils import Frame
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs
from dialogue_gen.dialogueline import Line
from dialogue_gen.characterinfo import CharacterInfo
from dialogue_gen.sysline import SysLine, Wait
from vidpy_extension.blankclip import transparent_clip
from vidpy_extension.ext_composition import ExtComposition
import configs
import durations
from exceptions import expect
from dialogue_gen.configcontext import ConfigContext


def filter_none(lines: list) -> list:
    return [line for line in lines if line is not None]


def generate(lines: list[Line]) -> ExtComposition:
    """Processes the list of lines into a Composition
    """
    context = ConfigContext()
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
    name = charInfo.name    # name after following alias

    headerFilter: dict = textFilterArgs(
        text=expect(charInfo.displayName, 'displayName', name),
        geometry=expect(charInfo.headerGeometry, 'headerGeometry', name),
        font=expect(charInfo.headerFont, 'headerFont', name),
        size=expect(charInfo.headerFontSize, 'headerFontSize', name),
        color=expect(charInfo.headerFillColor, 'headerFillColor', name),
        olcolor=expect(charInfo.headerOutlineColor, 'headerOutlineColor', name))

    dropTextFilter: dict = dropTextFilterArgs(
        resource=configs.follow_if_named(
            expect(charInfo.dropTextMaskPath, 'dropTextMaskPath', name)),
        end=expect(charInfo.dropTextEnd, 'dropTextEnd', name))

    richTextFilter: dict = richTextFilterArgs(
        text=line.text,
        geometry=expect(charInfo.dialogueGeometry, 'dialogueGeometry', name),
        font=expect(charInfo.dialogueFont, 'dialogueFont', name),
        fontSize=expect(charInfo.dialogueFontSize, 'dialogueFontSize', name),
        color=expect(charInfo.dialogueFontColor, 'dialogueFontColor', name))

    return Clip('color:#00000000', start=Frame(0)).set_duration(line.duration)\
        .fx('qtext', richTextFilter)\
        .fx('mask_start', dropTextFilter)\
        .fx('dynamictext', headerFilter)
