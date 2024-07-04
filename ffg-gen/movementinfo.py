from dataclasses import dataclass
from functools import cache
import configs


@dataclass
class MovementInfo:
    '''Movement info. 
    The intended usage is to access the instances through the static factory methods.
    Loads the properties from the config json on first access and caches the object as a singleton.
    '''

    # one of 'common' | 'player' | 'enemy'
    side: str

    # geometry
    geometry: str = None
    frontGeometry: str = None
    backGeometry:str = None
    offstageGeometry: str = None
    offstageBackGeometry: str = None

    # movement timing configs
    brightnessFadeEnd: str = None
    brightnessFadeLevel: float = None
    moveEnd: str = None
    exitDuration: float = None
    fadeInEnd: str = None
    fadeOutEnd: str = None

    def __post_init__(self):
        # if this is not the common movement info, then fall-through any unfilled properties to the common movement info
        if self.side != 'common':
            for attr, value in vars(self).items():
                if value is None:
                    setattr(self, attr, getattr(MovementInfo.ofCommon(), attr))

        # frontGeometry defaults to no transform
        if self.frontGeometry is None:
            self.frontGeometry = f'0 0 {configs.VIDEO_MODE.width} {configs.VIDEO_MODE.height} 1'

    @cache
    def ofCommon():
        '''Returns the singleton instance of the MovementInfo object.
        Will load info from the global config json.
        Make sure the json is loaded in before calling this!
        '''
        return MovementInfo(side='common', **configs.MOVEMENT.get('common'))

    @cache
    def ofIsPlayer(is_player: bool):
        '''Gets the global movement info for the given side.
        '''
        side: str = 'player' if is_player else 'enemy'
        return MovementInfo(side=side, **configs.MOVEMENT.get(side))