from vidpy import Clip
from dialogueline import DialogueLine
from sysline import SysLine
from vidpy_extension.ext_composition import ExtComposition
import configs
from exceptions import expect


def generate(lines: list[DialogueLine | SysLine], resource: str) -> ExtComposition:
    """Returns a Composition containing a single Clip.
    The lines are used to calculate the duration of the single Clip.
    """
    # caculate duration
    total_duration: float = sum([line.duration for line in lines if hasattr(line, 'duration')])

    # follow resource
    resource = configs.follow_if_named(resource)

    return ExtComposition(
        [Clip(resource).set_duration(total_duration)],
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)
