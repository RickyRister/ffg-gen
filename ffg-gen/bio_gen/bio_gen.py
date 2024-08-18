from typing import Generator
from argparse import ArgumentParser, _SubParsersAction
import json
from vidpy_extension.ext_composition import ExtComposition
import cli_args
import configs
import mlt_fix
from mlt_resource import MltResource
from exceptions import CliError
from lines import Line
from . import bconfigs
from . import line_parse
from bio_gen.generation import text_gen, fill_gen, portrait_gen, progressbar_gen, pagenum_gen


def attach_subparser_to(subparsers: _SubParsersAction, parents) -> None:
    '''Adds the command parser for bio scene to the subparser'''

    parser: ArgumentParser = subparsers.add_parser(
        'bio', help='Generate mlt for a bio scene', parents=parents)

    parser.add_argument(
        'components', nargs='+',
        help='''
        Determines which components to generate. Order does matter; layers go from top to bottom.

        You can configure macros in your config json under "componentMacros".
        Each macro maps to an array of components.
        Macros can be recursive :)
        ''')

    parser.add_argument(
        '--config', '-j', type=str, default='bio-gen.json',
        help='path to the config json')
    parser.add_argument(
        '--input', '-i', type=str, default='bio.txt',
        help='path to the input bio file')

    parser.set_defaults(func=bio_gen)


def bio_gen():
    # load config json into global config values
    with open(cli_args.ARGS.config) as json_file:
        json_dict = json.load(json_file)
        configs.load_into_globals(json_dict)
        bconfigs.load_into_globals(json_dict)

    # load lines from bio text file
    lines: list[Line]
    with open(cli_args.ARGS.input) as inputFile:
        lines = line_parse.parse_bio_file(inputFile)

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
            case 'progressbar': yield from gen_progressbar(lines)
            case 'pagenum': yield from gen_pagenums(lines)
            case x if x.startswith('portrait:'): yield from gen_portrait(lines, x.removeprefix('portrait:'))
            case x if x.startswith('fill:'): yield from gen_fill(lines, x.removeprefix('fill:'), False)
            case x if x.startswith('tfill:'): yield from gen_fill(lines, x.removeprefix('tfill:'), True)
            case 'groups': yield from gen_groups(lines)
            case x if x.startswith('group:'): yield from gen_group(lines, x.removeprefix('group:'))
            case _: raise CliError(f'{component} is not a valid component.')


#
# ===  gen_functions ===
# These functions all return generators, even the ones that can only possibly return one Composition
# Means that I don't have to check for None when iterating the result
#

def gen_text(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print(f"Generating text component")
    yield text_gen.generate(lines)


def gen_progressbar(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print(f"Generating progressbar component")
    yield progressbar_gen.generate(lines)


def gen_pagenums(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print(f"Generating pagenum component")
    yield pagenum_gen.generate(lines)


def gen_portrait(lines: list[Line], character: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating portrait component for {character}")
    yield portrait_gen.generate(lines, character)


def gen_fill(lines: list[Line], resource: str, do_fade: bool) -> Generator[ExtComposition, None, None]:
    print(f"Generating fill with {resource}")
    yield fill_gen.generate(lines, MltResource(resource), do_fade)


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
