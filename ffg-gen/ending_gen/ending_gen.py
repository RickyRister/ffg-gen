import json
from argparse import ArgumentParser, _SubParsersAction
from typing import Generator

import cli_args
import configs
import mlt_fix
from ending_gen.generation import fill_gen, tfill_gen, bgimage_gen, text_gen
from exceptions import CliError
from lines import Line
from mlt_resource import MltResource
from vidpy_extension.ext_composition import ExtComposition
from . import econfigs
from . import line_parse


def attach_subparser_to(subparsers: _SubParsersAction, parents) -> None:
    """Adds the command parser for ending scene to the subparser"""

    parser: ArgumentParser = subparsers.add_parser(
        'ending', help='Generate mlt for an ending scene', parents=parents)

    parser.add_argument(
        'components', nargs='+',
        help='''
        Determines which components to generate. Order does matter; layers go from top to bottom.

        You can configure macros in your config json under "componentMacros".
        Each macro maps to an array of components.
        Macros can be recursive :)
        ''')

    parser.add_argument(
        '--config', '-j', type=str, default='ending-gen.json',
        help='path to the config json')
    parser.add_argument(
        '--input', '-i', type=str, default='ending.txt',
        help='path to the input ending file')

    parser.set_defaults(func=ending_gen)


def ending_gen():
    # load config json into global config values
    with open(cli_args.ARGS.config) as json_file:
        json_dict = json.load(json_file)
        configs.load_into_globals(json_dict)
        econfigs.load_into_globals(json_dict)

    # load lines from ending text file
    lines: list[Line]
    with open(cli_args.ARGS.input) as inputFile:
        lines = line_parse.parse_ending_file(inputFile)

    # process the lines
    process_lines(lines)


def process_lines(lines: list[Line]):
    '''Processes the lines.
    Here in case we add chapter support in the future
    '''
    # generate all compositions
    compositions: list[ExtComposition] = list(process_components(cli_args.ARGS.components, lines))

    # reverse the list so components render in left-to-right order of cli args
    compositions.reverse()

    print("Done generating. Now exporting combined mlt...")

    mlt_fix.fix_and_write_mlt(compositions)


def process_components(components: list[str], lines: list[Line]) -> Generator[ExtComposition, None, None]:
    '''Creates a generator that will process each component.
    The generator yields the Composition for that component
    '''
    for component in components:
        match component:
            case macro if macro in configs.COMPONENT_MACROS:
                yield from process_components(configs.COMPONENT_MACROS.get(macro), lines)
            case 'text': yield from gen_text(lines)
            case 'bgimage': yield from gen_bgimage(lines)
            case x if x.startswith('fill:'): yield from gen_fill(lines, x.removeprefix('fill:'))
            case x if x.startswith('tfill:'): yield from gen_tfill(lines, x.removeprefix('tfill:'))
            case 'groups': yield from gen_groups(lines)
            case x if x.startswith('group:'): yield from gen_group(lines, x.removeprefix('group:'))
            case _: raise CliError(f'{component} is not a valid component.')


#
# ===  gen_functions ===
# These functions all return generators, even the ones that can only possibly return one Composition
# Means that I don't have to check for None when iterating the result
#

def gen_text(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print("Generating text component")
    yield from text_gen.generate(lines)


def gen_bgimage(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print("Generating bgimage component")
    yield bgimage_gen.generate(lines)


def gen_fill(lines: list[Line], resource: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating fill with {resource}")
    yield fill_gen.generate(lines, MltResource(resource))


def gen_tfill(lines: list[Line], resource: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating tfill with {resource}")
    yield tfill_gen.generate(lines, MltResource(resource))


def gen_groups(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print(f"Generating components for all component groups...")

    components: list[str] = [line.component for line in lines if hasattr(line, 'group')]
    yield from process_components(components, lines)


def gen_group(lines: list[Line], group: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating components for component group '{group}'")

    components: list[str] = [line.component for line in lines
                             if getattr(line, 'group', None) == group]
    if len(components) == 0:
        print(f"No components found for component group '{group}'")

    yield from process_components(components, lines)
