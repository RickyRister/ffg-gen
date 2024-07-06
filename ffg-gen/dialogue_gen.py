from argparse import ArgumentParser, _SubParsersAction
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, XML
from pathlib import Path
from typing import Callable, Generator
from vidpy import Composition
import configs
from dialogueline import DialogueLine, parseDialogueFile
from sysline import SysLine
from generation import text_gen, char_gen, header_gen
from characterinfo import CharacterInfo
from exceptions import DialogueGenException
import mlt_fix
from vidpy_extension.ext_composition import ExtComposition, compositions_to_mlt


def attach_subparser_to(subparsers: _SubParsersAction, parents) -> None:
    """Adds the command parser for dialogue scene to the subparser"""

    parser: ArgumentParser = subparsers.add_parser(
        'dialogue', help='Generate mlt for a dialogue scene', parents=parents)

    parser.add_argument(
        'components', nargs='+',
        help='"all" will generate all components. Otherwise, provide one or more options. Options: text, header, chars, char:[name]')

    parser.add_argument(
        '--use-blanks', action='store_const', const=True, default=False, dest='use_blanks',
        help='Use blanks for waits instead of transparent clips. May cause issues with durationFix if there are multiple consecutive blanks')

    parser.set_defaults(func=dialogue_gen)


def dialogue_gen():
    configs.loadConfigJson(configs.ARGS.config)

    lines = None
    with open(configs.ARGS.input) as inputFile:
        lines = parseDialogueFile(inputFile)

    composition_generator: Generator[tuple[ExtComposition, str]]
    composition_generator = process_components(configs.ARGS.components, lines)

    if configs.ARGS.separate_track_export:
        for (composition, file_suffix) in composition_generator:
            fix_and_write_mlt(composition.xml_as_element(), file_suffix)
    else:
        compositions: list[ExtComposition] = [genned[0] for genned in composition_generator]

        # reverse the list so components render in left-to-right order of cli args
        compositions.reverse()

        print("Done generating. Now exporting combined mlt...")

        xml: Element = compositions_to_mlt(compositions)
        fix_and_write_mlt(xml)


def process_components(components: list[str], lines: list[DialogueLine | SysLine]) -> Generator[tuple[ExtComposition, str], None, None]:
    '''Creates a generator that will process each component.
    The generator yields a tuple containing the Composition as well as the file_suffix for that component
    '''
    for component in components:
        match (str.lower(component)):
            case 'all': yield from gen_all(lines)
            case 'text': yield from gen_text(lines)
            case 'header': yield from gen_header(lines)
            case 'chars': yield from gen_chars(lines)
            case x if x.startswith('char:'): yield from gen_char(lines, x.removeprefix('char:'))
            case _: print(f'{component} is not a valid option; skipping')


def reset_configs():
    '''Resets any global configs that might have gotten altered during a run
    '''
    CharacterInfo.get_cached.cache_clear()


def fix_and_write_mlt(mlt: Element, file_suffix: str = None):
    '''Fixes and writes the mlt file generated by Composition
    '''
    fixed_xml: Element = mlt_fix.fix_mlt(mlt)

    suffix: str = '_' + file_suffix if file_suffix is not None else ''
    write_mlt(fixed_xml, suffix)


def write_mlt(xml: Element, suffix: str = ''):
    """Writes the xml to a file.
    The suffix is appended to the output name given by the cli args
    """
    path: Path = Path(configs.ARGS.output)
    path = path.with_stem(path.stem + suffix)

    with open(path, 'wb') as outfile:
        xml_string = ElementTree.tostring(xml)
        outfile.write(xml_string)

#
# ===  gen_functions ===
# These functions all return generators, even the ones that can only possibly return one Composition
# Means that I don't have to check for None when iterating the result
# The generators return tuples of (Composition, file_suffix)
#


def wrap_generate(gen_function: Callable[[list], Composition],
                  file_suffix: str, error_msg: str) -> Generator[tuple[ExtComposition, str], None, None]:
    '''Wraps the generate() call to do all the error handling stuff'''
    try:
        yield (gen_function(), file_suffix)
    except DialogueGenException as e:
        print(error_msg, e)
        if configs.ARGS.debug or not configs.ARGS.separate_track_export:
            raise e
    finally:
        reset_configs()


def gen_all(lines: list[DialogueLine | SysLine]) -> Generator[tuple[ExtComposition, str], None, None]:
    print("Generating all components...")
    yield from gen_text(lines)
    yield from gen_header(lines)
    yield from gen_chars(lines)


def gen_text(lines: list[DialogueLine | SysLine]) -> Generator[tuple[ExtComposition, str], None, None]:
    print("Generating text component")
    yield from wrap_generate(lambda: text_gen.generate(lines), 'text',
                             'Error while generating text:')


def gen_header(lines: list[DialogueLine | SysLine]) -> Generator[tuple[ExtComposition, str], None, None]:
    print("Generating header overlay component")
    yield from wrap_generate(lambda: header_gen.generate(lines), 'header',
                             'Error while generating header overlay:')


def gen_chars(lines: list[DialogueLine | SysLine]) -> Generator[tuple[ExtComposition, str], None, None]:
    print("Generating all character components...")

    # figure out which characters are in the dialogue
    names: set[str] = {line.name for line in lines if hasattr(line, 'name')}

    # call gen_char with all those characters
    for name in names:
        yield from gen_char(lines, name)


def gen_char(lines: list[DialogueLine | SysLine], character: str) -> Generator[tuple[ExtComposition, str], None, None]:
    print(f"Generating character component for {character}")
    yield from wrap_generate(lambda: char_gen.generate(lines, character), character,
                             f'Error while generating character component for {character}:')
