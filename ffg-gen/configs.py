from typing import Union
from argparse import Namespace
from dataclasses import dataclass
import json

# parsed command line args
ARGS: Namespace


@dataclass
class VideoModeConfigs:
    width: int
    height: int
    fps: int


@dataclass
class HeaderConfigs:
    geometry: str
    font: str
    fontSize: int
    weight: int


@dataclass
class DialogueBoxConfigs:
    geometry: str
    dropTextMaskPath: str
    dropTextEnd: str
    font: str
    fontSize: int


@dataclass
class Threshold:
    """Contains info about mapping count to duration, as well as info about converting frame durations to timestamp durations.
    The expected out frame won't be known at first.
    We recommend you run the tool first to fill in the expected frame and the correct fix.
    """

    count: int
    duration: float
    expectedFrames: int = None  # expected out frame
    fix: str = None             # timestamp fix


@dataclass
class DurationConfigs:
    mode: str
    thresholds: list[Threshold]

    def __post_init__(self):
        if isinstance(self.thresholds[0], dict):
            self.thresholds = [Threshold(**threshold)
                               for threshold in self.thresholds]


@dataclass
class CommonMovementConfigs:
    brightnessFadeEnd: str
    brightnessFadeLevel: float
    moveEnd: str


@dataclass
class CharacterMovementConfigs:
    backGeometry: str
    offstageGeometry: str
    frontGeometry: str = None


# dialogue regex
DIALOGUE_REGEX: str

# more specific configs
VIDEO_MODE: VideoModeConfigs
HEADER: HeaderConfigs
DIALOGUE_BOX: DialogueBoxConfigs
DURATIONS: DurationConfigs
MOVEMENT: CommonMovementConfigs
PLAYER_MOVEMENT: CharacterMovementConfigs
ENEMY_MOVEMENT: CharacterMovementConfigs

# character configs are still stored as a dict
CHARACTERS: dict[str, dict]


def loadConfigJson(path: str):
    """Reads the json file into appropriate configs
    path: path to the json file
    """

    configJson: dict = None
    with open(path) as configFile:
        configJson = json.load(configFile)

    # bring globals into scope
    global DIALOGUE_REGEX
    global VIDEO_MODE
    global HEADER
    global DIALOGUE_BOX
    global DURATIONS
    global MOVEMENT
    global PLAYER_MOVEMENT
    global ENEMY_MOVEMENT
    global CHARACTERS

    # assigne globals
    DIALOGUE_REGEX = configJson.get('dialogueRegex')
    VIDEO_MODE = VideoModeConfigs(**configJson.get('videoMode'))
    HEADER = HeaderConfigs(**configJson.get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**configJson.get('dialogueBox'))
    DURATIONS = DurationConfigs(**configJson.get('durations'))
    MOVEMENT = CommonMovementConfigs(**configJson.get('movement').get('common'))
    PLAYER_MOVEMENT = CharacterMovementConfigs(**configJson.get('movement').get('player'))
    ENEMY_MOVEMENT = CharacterMovementConfigs(**configJson.get('movement').get('enemy'))

    CHARACTERS = configJson.get('characters')
