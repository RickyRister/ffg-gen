from dataclasses import dataclass

'''Configs that are common to all operations
'''


# =======
# Classes
# =======

@dataclass
class VideoModeConfigs:
    width: int
    height: int
    fps: int = 30


# =======================
# Common Global Constants
# =======================

# common configs
VIDEO_MODE: VideoModeConfigs

# not handled by own class but still stored as a raw data structure
COMPONENT_MACROS: dict[str, list[str]]
RESOURCE_NAMES: dict[str, str]
GLOBAL_ALIASES: dict[str, str]


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
    global VIDEO_MODE
    global COMPONENT_MACROS
    global RESOURCE_NAMES
    global GLOBAL_ALIASES

    # assign globals
    VIDEO_MODE = VideoModeConfigs(**safe_json_get('videoMode'))

    # load dicts
    COMPONENT_MACROS = safe_json_get('componentMacros')
    RESOURCE_NAMES = safe_json_get('resourceNames')

    # load dicts for the classes to load themselves
    GLOBAL_ALIASES = safe_json_get('aliases')


# ========
# Getters
# ========

def follow_global_alias(name: str):
    '''Follows any global aliases.
    Aliases are recursive.
    '''

    if name in GLOBAL_ALIASES:
        return follow_global_alias(GLOBAL_ALIASES.get(name))

    return name
