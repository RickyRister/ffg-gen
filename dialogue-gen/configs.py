from typing import Union
from argparse import Namespace
from dataclasses import dataclass
from functools import cache
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
    count: int
    duration: str


@dataclass
class DurationConfigs:
    mode: str
    thresholds: list[Threshold]

    def __post_init__(self):
        if isinstance(self.thresholds[0], dict):
            self.thresholds = [Threshold(**threshold)
                               for threshold in self.thresholds]


# dialogue regex
DIALOGUE_REGEX: str

# more specific configs
VIDEO_MODE: VideoModeConfigs
HEADER: HeaderConfigs
DIALOGUE_BOX: DialogueBoxConfigs
DURATIONS: DurationConfigs

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
    global CHARACTERS

    # assigne globals
    DIALOGUE_REGEX = configJson.get('dialogueRegex')
    VIDEO_MODE = VideoModeConfigs(**configJson.get('videoMode'))
    HEADER = HeaderConfigs(**configJson.get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**configJson.get('dialogueBox'))
    DURATIONS = DurationConfigs(**configJson.get('durations'))
    CHARACTERS = configJson.get('characters')
