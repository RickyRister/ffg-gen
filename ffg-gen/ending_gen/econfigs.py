from dataclasses import dataclass

from durations import Durations

'''Configs that are specific to ending_gen
'''


# === Classes ===

@dataclass
class ParsingConfigs:
    dialogueRegex: str  # used to determine if a speaker change is needed


# === Global Constants ===

# more specific configs
PARSING: ParsingConfigs
DURATIONS: Durations

# configs that are loaded by their own classes are still stored as a dict
ENDING_INFO: dict[str, dict]
CHARACTERS: dict[str, dict]


def load_into_globals(configJson: dict):
    '''Load the json config values into the global variables
    '''

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
    global ENDING_INFO
    global CHARACTERS

    # assign globals
    PARSING = ParsingConfigs(**safe_json_get('parsing'))
    DURATIONS = Durations(**safe_json_get('durations'))

    # load dicts for the classes to load themselves
    ENDING_INFO = safe_json_get('endingInfo')
    CHARACTERS = safe_json_get('characters')
