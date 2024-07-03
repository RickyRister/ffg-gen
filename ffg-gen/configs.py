from argparse import Namespace
from dataclasses import dataclass
import json
import re
from duration import DurationFix, Threshold

# parsed command line args
ARGS: Namespace

# loaded config json
CONFIG_JSON: dict


@dataclass
class ParsingConfigs:
    dialogueRegex: str
    shortDialogueRegex: str
    expressionRegex: str
    assignmentDelimiter: str = '='


@dataclass
class VideoModeConfigs:
    width: int
    height: int
    fps: int = 30


@dataclass
class DurationConfigs:
    mode: str
    thresholds: list[Threshold]

    def __post_init__(self):
        # convert dict to actual objects, if nessecary
        if isinstance(self.thresholds[0], dict):
            self.thresholds = [Threshold(**threshold) for threshold in self.thresholds]


@dataclass
class HeaderConfigs:
    geometry: str
    font: str
    fontSize: int
    weight: int = 500
    outlineColor: str = '#000000'
    fillColor: str = '#ffffff'


@dataclass
class DialogueBoxConfigs:
    geometry: str
    dropTextMaskPath: str
    dropTextEnd: str
    font: str
    fontSize: int
    fontColor: str = '#ffffff'


@dataclass
class CommonMovementConfigs:
    brightnessFadeEnd: str
    brightnessFadeLevel: float
    moveEnd: str
    exitDuration: float
    fadeInEnd: str
    fadeOutEnd: str
    geometry: str | None = None
    frontGeometry: str = None

    def __post_init__(self):
        # frontGeometry defaults to no transform
        if self.frontGeometry is None:
            self.frontGeometry = f'0 0 {VIDEO_MODE.width} {VIDEO_MODE.height} 1'


@dataclass
class CharacterMovementConfigs:
    backGeometry: str
    offstageGeometry: str
    geometry: str | None = None
    frontGeometry: str = None
    offstageBackGeometry: str = None

    def __post_init__(self):
        '''All unfilled properties will fall through to the common movement configs
        '''
        # offstageBackGeometry will default to the same as offstageGeometry if not set
        if self.offstageBackGeometry is None:
            self.offstageBackGeometry = self.offstageGeometry

        # fall through to defaults
        if self.geometry is None:
            self.geometry = MOVEMENT.geometry
        if self.frontGeometry is None:
            self.frontGeometry = MOVEMENT.frontGeometry


# more specific configs
PARSING: ParsingConfigs
VIDEO_MODE: VideoModeConfigs
DURATIONS: DurationConfigs
DURATION_FIXES: list[DurationFix]
HEADER: HeaderConfigs
DIALOGUE_BOX: DialogueBoxConfigs
MOVEMENT: CommonMovementConfigs
PLAYER_MOVEMENT: CharacterMovementConfigs
ENEMY_MOVEMENT: CharacterMovementConfigs

# character configs are still stored as a dict
CHARACTERS: dict[str, dict]


def loadConfigJson(path: str):
    """Reads the json file into appropriate configs, then loads the json values into the globals
    path: path to the json file
    """

    global CONFIG_JSON
    with open(path) as configFile:
        CONFIG_JSON = json.load(configFile)

    loadIntoGlobals(CONFIG_JSON)


def loadIntoGlobals(configJson: dict):
    """Load the json config values into the global variables
    """
    # bring globals into scope
    global PARSING
    global VIDEO_MODE
    global DURATIONS
    global DURATION_FIXES
    global HEADER
    global DIALOGUE_BOX
    global MOVEMENT
    global PLAYER_MOVEMENT
    global ENEMY_MOVEMENT
    global CHARACTERS

    # assign globals
    PARSING = ParsingConfigs(**configJson.get('parsing'))
    VIDEO_MODE = VideoModeConfigs(**configJson.get('videoMode'))
    DURATIONS = DurationConfigs(**configJson.get('durations'))
    DURATION_FIXES = [DurationFix(**fix) for fix in configJson.get('durationFixes')]
    HEADER = HeaderConfigs(**configJson.get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**configJson.get('dialogueBox'))
    MOVEMENT = CommonMovementConfigs(**configJson.get('movement').get('common'))
    PLAYER_MOVEMENT = CharacterMovementConfigs(**configJson.get('movement').get('player'))
    ENEMY_MOVEMENT = CharacterMovementConfigs(**configJson.get('movement').get('enemy'))

    CHARACTERS = configJson.get('characters')


def get_char_move(is_player: bool) -> CharacterMovementConfigs:
    return PLAYER_MOVEMENT if is_player else ENEMY_MOVEMENT
