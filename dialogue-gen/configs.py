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
class TimingConfigs:
    inEnd: str


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
    font: str
    fontSize: int


# dialogue regex
DIALOGUE_REGEX: str

# more specific configs
VIDEO_MODE: VideoModeConfigs
TIMING: TimingConfigs
HEADER: HeaderConfigs
DIALOGUE_BOX: DialogueBoxConfigs

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
    global TIMING
    global HEADER
    global DIALOGUE_BOX
    global CHARACTERS

    # assigne globals
    DIALOGUE_REGEX = configJson.get('dialogueRegex')
    VIDEO_MODE = VideoModeConfigs(**configJson.get('videoMode'))
    TIMING = TimingConfigs(**configJson.get('timing'))
    HEADER = HeaderConfigs(**configJson.get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**configJson.get('dialogueBox'))
    CHARACTERS = configJson.get('characters')
