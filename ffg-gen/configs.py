from argparse import Namespace
from dataclasses import dataclass
import json
from typing import TypeVar
from duration import DurationFix, Threshold

T = TypeVar("T")

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
    font: str = None
    fontSize: int = None
    weight: int = 500
    outlineColor: str = None
    fillColor: str = '#ffffff'


@dataclass
class DialogueBoxConfigs:
    geometry: str
    dropTextMaskPath: str
    dropTextEnd: str
    font: str = None
    fontSize: int = None
    fontColor: str = '#ffffff'


# more specific configs
PARSING: ParsingConfigs
VIDEO_MODE: VideoModeConfigs
DURATIONS: DurationConfigs
DURATION_FIXES: list[DurationFix]
HEADER: HeaderConfigs
DIALOGUE_BOX: DialogueBoxConfigs

# configs that are loaded by their own classes are still stored as a dict
MOVEMENT: dict[str, dict]
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
    global CHARACTERS

    # assign globals
    PARSING = ParsingConfigs(**configJson.get('parsing'))
    VIDEO_MODE = VideoModeConfigs(**configJson.get('videoMode'))
    DURATIONS = DurationConfigs(**configJson.get('durations'))
    DURATION_FIXES = [DurationFix(**fix) for fix in configJson.get('durationFixes')]
    HEADER = HeaderConfigs(**configJson.get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**configJson.get('dialogueBox'))

    # load dicts for the classes to load themselves
    MOVEMENT = configJson.get('movement')
    CHARACTERS = configJson.get('characters')


def expect(value: T, prop_name: str, char_name: str = None) -> T:
    '''Use this to validate that a property is not None before using it.
    Raises an exception if it is None.

    args:
        value: The value to validate
        prop_name: name of the property, for error message purposes
        char_name: character name, if the property belongs to a character
    '''
    if value is not None:
        return value
    elif char_name is not None:
        raise ValueError(f'Could not resolve property {prop_name} for character {char_name}')
    else:
        raise ValueError(f'Could not resolve property {prop_name}')
