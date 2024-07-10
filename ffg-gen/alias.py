import configs


local_aliases: dict[str, str] = dict()
tracked_nicks: dict[str, str] = dict()


def follow_alias(name: str, follow_local: bool = True):
    '''Follows any aliases.
    Checks the local aliases first.
    Aliases are recursive.
    '''
    if follow_local and name in local_aliases:
        return follow_alias(local_aliases.get(name))

    if name in configs.GLOBAL_ALIASES:
        return follow_alias(configs.GLOBAL_ALIASES.get(name))

    return name


def add_local_alias(name: str, alias: str):
    '''Set local alias. The local alias dict is (ironically enough) a global variable.
    '''
    local_aliases[alias] = name


def remove_local_alias(alias: str):
    '''Removes a local alias
    '''
    local_aliases.pop(alias)


def track_nick(name: str, nick: str):
    '''Adds the nick to the name -> nick dict
    '''
    tracked_nicks[name] = nick


def pop_nick(name: str) -> str:
    '''Removes the nick from the dict
    '''
    tracked_nicks.pop(name, None)


def reset_all_local():
    '''Removes all local aliases as well as tracked nicknames
    '''
    local_aliases.clear()
    tracked_nicks.clear()
