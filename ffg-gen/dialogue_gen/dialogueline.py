from dataclasses import dataclass
from bisect import bisect
import re
import configs
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
        match configs.DURATIONS.mode:
            case 'char':
                count = len(self.text)
            case 'word':
                count = len(re.findall(r'\w+', self.text))
            case _:
                raise ValueError(f'{configs.DURATIONS.mode} is not a valid durations mode')

        index = bisect(configs.DURATIONS.thresholds, count,
                       key=lambda threshold: threshold.count)
        return configs.DURATIONS.thresholds[index-1].duration
