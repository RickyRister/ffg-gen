from durations import Durations

'''Configs that are specific to bio_gen
'''


# === Global Constants ===

# more specific configs
DURATIONS: Durations

# configs that are loaded by their own classes are still stored as a dict
BIO_INFO: dict[str, dict]
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
    global DURATIONS
    global BIO_INFO
    global CHARACTERS

    # assign globals
    DURATIONS = Durations(**safe_json_get('durations'))

    # load dicts for the classes to load themselves
    BIO_INFO = safe_json_get('bioInfo')
    CHARACTERS = safe_json_get('characters')
