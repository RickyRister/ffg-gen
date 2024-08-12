from vidpy import Clip
from dialogueline import DialogueLine
from sysline import SysLine
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
import configs
import durations
from characterinfo import CharacterInfo


def generate(lines: list[DialogueLine | SysLine], resource: str) -> ExtComposition:
    """Returns a Composition containing a single Clip.
    The lines are used to calculate the duration of the single Clip.
    """
    # caculate duration
    all_durations: list[Frame] = [line.duration for line in lines if hasattr(line, 'duration')]
    # also add the time taken for the exit
    all_durations.append(durations.to_frame(CharacterInfo.of_common().exitDuration))
    total_duration: Frame = sum(all_durations)

    # the gap between each clip is 1 frame, so we also need to make up those durations
    total_duration += Frame(len(all_durations) - 1)

    # follow resource
    resource = configs.follow_if_named(resource)

    return ExtComposition(
        [Clip(resource, start=Frame(0)).set_duration(total_duration)],
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)
