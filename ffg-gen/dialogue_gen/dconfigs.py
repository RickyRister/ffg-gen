from dataclasses import dataclass
from durations import Threshold

'''Configs that are specific to dialogue_gen
'''


# === Classes ===

@dataclass
class ParsingConfigs:
    dialogueRegex: str
    shortDialogueRegex: str
    expressionRegex: str


@dataclass
class DurationConfigs:
    mode: str
    thresholds: list[Threshold]

    def __post_init__(self):
        # convert dict to actual objects, if nessecary
        if isinstance(self.thresholds[0], dict):
            self.thresholds = [Threshold(**threshold) for threshold in self.thresholds]


# === Global Constants ===

# more specific configs
PARSING: ParsingConfigs
DURATIONS: DurationConfigs

# configs that are loaded by their own classes are still stored as a dict
CHAR_INFO: dict[str, dict]
CHARACTERS: dict[str, dict]


def load_into_globals(configJson: dict):
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
    global DURATIONS
    global CHAR_INFO
    global CHARACTERS

    # assign globals
    PARSING = ParsingConfigs(**safe_json_get('parsing'))
    DURATIONS = DurationConfigs(**safe_json_get('durations'))

    # load dicts for the classes to load themselves
    CHAR_INFO = safe_json_get('charInfo')
    CHARACTERS = safe_json_get('characters')
