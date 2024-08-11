from typing import Self
from functools import cache
from characterinfo import CharacterInfo
import configs


class ConfigContext:
    '''Encapsulates all the config changes that happens during a run
    so that we're not modifying the global state and then have to remember to reset it between each run

    Tracks changes to characterInfo and aliases
    '''

    def __init__(self) -> Self:
        '''Creates a new context, with the values starting as the global config values
        '''
        self.local_aliases: dict[str, str] = dict()
        self.tracked_nicks: dict[str, str] = dict()
        self.cached_chars: dict[str, CharacterInfo] = dict()

    def get_char(self, name: str, follow_alias: bool = True) -> CharacterInfo:
        '''Gets the CharacterInfo from this context corresponding to the name.
        Will follow aliases.
        '''
        name = str.lower(name)

        if follow_alias:
            name = self.follow_alias(name)

        # create new CharacterInfo from default values if not present in cache
        if name not in self.cached_chars:
            self.cached_chars[name] = CharacterInfo.of_name(name)

        return self.cached_chars.get(name)

    def reset_all_char(self):
        '''Resets all CharacterInfo by clearing the cache
        '''
        self.cached_chars.clear()

    def follow_alias(self, name: str) -> str:
        '''Follows any aliases.
        Checks the local aliases first.
        Aliases are recursive.
        '''
        if name in self.local_aliases:
            return self.follow_alias(self.local_aliases.get(name))

        if name in configs.GLOBAL_ALIASES:
            return self.follow_alias(configs.GLOBAL_ALIASES.get(name))

        return name

    def add_local_alias(self, name: str, alias: str):
        '''Set local alias
        '''
        self.local_aliases[alias] = name

    def remove_local_alias(self, alias: str):
        '''Removes a local alias
        '''
        self.local_aliases.pop(alias)

    def track_nick(self, name: str, nick: str):
        '''Adds the nick to the name -> nick dict
        '''
        self.tracked_nicks[name] = nick

    def pop_nick(self, name: str) -> str:
        '''Removes the nick from the dict

        return: the removed nick
        '''
        self.tracked_nicks.pop(name, None)
