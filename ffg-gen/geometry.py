from dataclasses import dataclass, field
from typing import Self
import configs


@dataclass(frozen=True)
class Geometry:
    '''Represents a Geometry in Shotcut
    '''
    x: float
    y: float
    width: float = field(default_factory=lambda: configs.VIDEO_MODE.width)
    height: float = field(default_factory=lambda: configs.VIDEO_MODE.height)

    @staticmethod
    def parse(input: str | Self | None) -> Self | None:
        '''Safely parses a string into a Geometry.
        Expects the string to contain each number in order, delimited by spaces.
        Ignores all values after the 4th one 

        Only x and y are mandatory; will use screen size for height and width by default

        Also accepts Geometry and None for ease of use.

        Geometry will return itself.
        None will return None
        '''
        # deal with the corner cases first
        if input is None:
            return None
        elif isinstance(input, Geometry):
            return input

        match input.split(None):
            case [x, y, width, height, *_]:
                return Geometry(x, y, width, height)
            case [x, y]:
                return Geometry(x, y)
            case _:
                raise ValueError(f'Cannot parse string into Geometry: {input}')

    def __str__(self):
        '''String representation that allows it to be used by shotcut
        '''
        return f'{self.x} {self.y} {self.width} {self.height}'
