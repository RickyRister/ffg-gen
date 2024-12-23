from vidpy import Clip
from lines import Line
from vidpy.utils import Frame
from vidpy_extension.ext_composition import ExtComposition
import configs
from mlt_resource import MltResource


def generate(lines: list[Line], resource: MltResource) -> ExtComposition:
    """Returns a Composition containing a single Clip.
    The lines are used to calculate the duration of the single Clip.
    """
    # caculate duration
    all_durations: list[Frame] = [line.duration for line in lines if hasattr(line, 'duration')]

    # TODO: also add the time taken for the exit
    total_duration: Frame = sum(all_durations)

    # the gap between each clip is 1 frame, so we also need to make up those durations
    total_duration += Frame(len(all_durations) - 1)

    return ExtComposition(
        [Clip(str(resource), start=Frame(0)).set_duration(total_duration)],
        singletrack=True,
        width=configs.VIDEO_MODE.width,
        height=configs.VIDEO_MODE.height,
        fps=configs.VIDEO_MODE.fps)
