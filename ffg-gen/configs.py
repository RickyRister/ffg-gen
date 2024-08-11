import math
from argparse import Namespace
from dataclasses import dataclass
import json
from vidpy.utils import Second, Frame
from duration import DurationFix, Threshold
from exceptions import MissingProperty

# parsed command line args
ARGS: Namespace

# loaded config json
CONFIG_JSON: dict


# === Classes ===

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
    unit: str
    thresholds: list[Threshold]

    def __post_init__(self):
        # convert dict to actual objects, if nessecary
        if isinstance(self.thresholds[0], dict):
            self.thresholds = [Threshold(**threshold) for threshold in self.thresholds]

    def convert_duration(self, duration: int | float) -> Frame | Second:
        '''Converts the duration into either seconds or frames, accounting for the settings

        If duration is an int: interpret as frames. 
        Directly convert to a Frame regardless of the unit.

        If duration is a float: interpret as seconds. 
        If the unit is frames, will multiply the duration by the fps before converting to Second
        '''
        if isinstance(duration, int):
            return Frame(duration)
        else:
            if self.unit == 'frames':
                # we subtract 1 from the resulting frame if it lands on an integer
                return Frame(math.floor(duration * VIDEO_MODE.fps - 0.000001))
            else:
                return Second(duration)


@dataclass
class DurationFixConfigs:
    fixes: list[DurationFix] = None
    fallbackMultiplier: float = None

    def __post_init__(self):
        # convert dict to actual objects, if nessecary
        if self.fixes is None:
            self.fixes = []
        elif isinstance(self.fixes[0], dict):
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


# === Global Constants ===

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
GLOBAL_ALIASES: dict[str, str]


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

    # make sure the json get is null-checked
    def safe_json_get(key: str) -> dict:
        value = configJson.get(key)
        if value is None:
            return dict()
        else:
            return value

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
    global GLOBAL_ALIASES

    # assign globals
    PARSING = ParsingConfigs(**safe_json_get('parsing'))
    VIDEO_MODE = VideoModeConfigs(**safe_json_get('videoMode'))
    DURATIONS = DurationConfigs(**safe_json_get('durations'))
    DURATION_FIX = DurationFixConfigs(**safe_json_get('durationFix'))
    HEADER = HeaderConfigs(**safe_json_get('header'))
    DIALOGUE_BOX = DialogueBoxConfigs(**safe_json_get('dialogueBox'))

    # load dicts
    COMPONENT_MACROS = safe_json_get('componentMacros')
    RESOURCE_NAMES = safe_json_get('resourceNames')

    # load dicts for the classes to load themselves
    MOVEMENT = safe_json_get('movement')
    CHARACTERS = safe_json_get('characters')
    GLOBAL_ALIASES = safe_json_get('aliases')


# === Getters ===

def follow_if_named(resource: str) -> str:
    '''Converts the resource to the proper link if it's a named resource.

    Named resources are indicated by starting with a !
    You can terminate the name with another !
    '''

    # return early if it's not a named resource
    if not resource.startswith('!'):
        return resource

    # parse string
    split = resource[1:].split('!', 1)
    name: str = split[0]
    postfix: str = split[1] if len(split) > 1 else ''

    # get name
    if name not in RESOURCE_NAMES:
        raise MissingProperty(f"Named resource '{name}' not defined.")
    else:
        return RESOURCE_NAMES.get(name) + postfix


def follow_alias(name: str):
    '''Follows any global aliases.
    Aliases are recursive.
    '''

    if name in GLOBAL_ALIASES:
        return follow_alias(GLOBAL_ALIASES.get(name))

    return name
