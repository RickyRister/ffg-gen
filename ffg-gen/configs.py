from argparse import Namespace
from dataclasses import dataclass
import json
from duration import DurationFix, Threshold
from exceptions import MissingProperty

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
class DurationFixConfigs:
    fixes: list[DurationFix]
    fallbackMultiplier: float = None

    def __post_init__(self):
        # convert dict to actual objects, if nessecary
        if isinstance(self.fixes[0], dict):
            self.fixes = [DurationFix(**fix) for fix in self.fixes]


@dataclass
class HeaderConfigs:
    geometry: str
    font: str = None
    fontSize: int = None
    weight: int = 500
    outlineColor: str = None
    fillColor: str = '#ffffff'
    overlayPath: str = None


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
DURATION_FIX: DurationFixConfigs
HEADER: HeaderConfigs
DIALOGUE_BOX: DialogueBoxConfigs

# configs that are loaded by their own classes are still stored as a dict
MOVEMENT: dict[str, dict]
CHARACTERS: dict[str, dict]

# not handled by own class but still stored as a raw data structure
COMPONENT_MACROS: dict[str, list[str]]
RESOURCE_NAMES: dict[str, str]


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
    global DURATION_FIX
    global HEADER
    global DIALOGUE_BOX
    global MOVEMENT
    global CHARACTERS
    global COMPONENT_MACROS
    global RESOURCE_NAMES

    # assign globals
    PARSING = ParsingConfigs(**configJson.get('parsing'))
    VIDEO_MODE = VideoModeConfigs(**configJson.get('videoMode'))
    DURATIONS = DurationConfigs(**configJson.get('durations'))
    DURATION_FIX = DurationFixConfigs(**configJson.get('durationFix'))
    HEADER = HeaderConfigs(**configJson.get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**configJson.get('dialogueBox'))

    # load dicts
    COMPONENT_MACROS = configJson.get('componentMacros')
    RESOURCE_NAMES = configJson.get('resourceNames')

    # load dicts for the classes to load themselves
    MOVEMENT = configJson.get('movement')
    CHARACTERS = configJson.get('characters')


def follow_if_named(resource: str) -> str:
    '''Converts the resource to the proper link if it's a named resource.

    Named resources are indicated by starting with a !
    '''

    # return early if it's not a named resource
    if not resource.startswith('!'):
        return resource

    # get name
    name: str = resource[1:]
    if name not in RESOURCE_NAMES:
        raise MissingProperty(f'Named resource "{name}" not found.')
    else:
        return RESOURCE_NAMES.get(name)
