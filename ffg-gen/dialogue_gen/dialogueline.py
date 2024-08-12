from dataclasses import dataclass
from bisect import bisect
import re
from dialogue_gen import dconfigs
from vidpy.utils import Frame


@dataclass
class DialogueLine:
    """A single parsed line from the script.
    The fields are parsed by using the regex in the config json.
    only the expression field is optional
    """
    name: str
    expression: str | None
    text: str

    @property
    def duration(self) -> Frame:
        """Determines how long the text should last for depending on its length.
        Duration unit depends on configs 
        """

        count: int = None
        match dconfigs.DURATIONS.mode:
            case 'char':
                count = len(self.text)
            case 'word':
                count = len(re.findall(r'\w+', self.text))
            case _:
                raise ValueError(f'{dconfigs.DURATIONS.mode} is not a valid durations mode')

        index = bisect(dconfigs.DURATIONS.thresholds, count,
                       key=lambda threshold: threshold.count)
        return dconfigs.DURATIONS.thresholds[index-1].duration
