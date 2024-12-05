from typing import Self
from dataclasses import dataclass, replace
import configs
from exceptions import MissingConfigError


@dataclass
class MltResource:
    '''Represents a resource that is used by mlt.

    This class automatically handles resolving named resources.
    '''
    resource: str

    def __post_init__(self):
        # prevent nested Resource classes
        if isinstance(self.resource, MltResource):
            self.resource = self.resource.resource

    def __str__(self) -> str:
        return MltResource.follow_if_named(self.resource)

    def format(self, **kwargs) -> Self:
        '''Runs str.format() on the internal resource string.

        returns: A new instance of this class with the changes 
        '''
        formatted: str = str.format(self.resource, **kwargs)
        return replace(self, resource=formatted)

    @staticmethod
    def follow_if_named(resource: str) -> str:
        '''Converts the resource to the proper link if it's a named resource.

        Named resources are indicated by starting with a !
        You can terminate the name with another !

        Named resources are recursive :)
        '''

        # return early if it's not a named resource
        if not resource.startswith('!'):
            return resource

        # parse string
        split = resource[1:].split('!', 1)
        name: str = split[0]
        postfix: str = split[1] if len(split) > 1 else ''

        # get name
        if name not in configs.RESOURCE_NAMES:
            raise MissingConfigError(f"Named resource '{name}' not defined.")
        else:
            resource = MltResource.follow_if_named(configs.RESOURCE_NAMES.get(name))
            return resource + postfix
