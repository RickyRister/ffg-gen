import configs


local_aliases: dict[str, str] = dict()


def follow_alias(name: str):
    '''Follows any aliases.
    Checks the local aliases first.
    Aliases are recursive.
    '''
    if name in local_aliases:
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
    del local_aliases[alias]


def remove_local_aliases_for_name(name: str):
    '''Removes all local aliases for the given name
    '''
    for key, value in list(local_aliases.items()):
        if value == name:
            del local_aliases[key]


def reset_local_aliases():
    '''Removes all local aliases
    '''
    local_aliases.clear()
