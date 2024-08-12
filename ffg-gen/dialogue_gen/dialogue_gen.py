from argparse import ArgumentParser, _SubParsersAction
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from pathlib import Path
from typing import Generator
import json
import cli_args
import configs
from dialogue_gen import dconfigs
from dialogue_gen.dialogueline import Line
from dialogue_gen import line_parse
from dialogue_gen.generation import text_gen, char_gen, header_gen, fill_gen, tfill_gen
from dialogue_gen.characterinfo import CharacterInfo
import mlt_fix
from vidpy_extension.ext_composition import ExtComposition, compositions_to_mlt


def attach_subparser_to(subparsers: _SubParsersAction, parents) -> None:
    """Adds the command parser for dialogue scene to the subparser"""

    parser: ArgumentParser = subparsers.add_parser(
        'dialogue', help='Generate mlt for a dialogue scene', parents=parents)

    parser.add_argument(
        'components', nargs='+',
        help='''
        Determines which components to generate. Order does matter; layers go from top to bottom.
        Built-in options: text, header, char:[name], chars, fill:[resource], group:[group], groups

        You can configure macros in your config json under "componentMacros".
        Each macro maps to an array of components.
        Macros can be recursive :)
        ''')

    parser.add_argument(
        '--config', '-j', type=str, default='dialogue-gen.json',
        help='path to the config json')
    parser.add_argument(
        '--input', '-i', type=str, default='dialogue.txt',
        help='path to the input dialogue file')
    parser.add_argument(
        '--fill-blanks', action='store_const', const=True, default=False, dest='fill_blanks',
        help='Use transparent clips for waits instead of blanks.')
    parser.add_argument(
        '--chapter', '-c', type=str, default=None,
        help='Only generate this chapter')

    parser.set_defaults(func=dialogue_gen)


def dialogue_gen():
    # load config json into global config values
    with open(cli_args.ARGS.config) as json_file:
        json_dict = json.load(json_file)
        configs.load_into_globals(json_dict)
        dconfigs.load_into_globals(json_dict)

    # load lines from dialogue text file
    common_lines: list[Line] = None
    chapters: dict[str, list[Line]] = None
    with open(cli_args.ARGS.input) as inputFile:
        common_lines, chapters = line_parse.parseDialogueFile(inputFile)

    # determine which chapters to process
    if (chapter_name := cli_args.ARGS.chapter) is not None:
        # cli args; only process this chapter
        if chapter_name not in chapters:
            raise ValueError(f'{chapter_name} is not a valid chapter.')

        print(f'=== Generating for chapter: {chapter_name} ===')
        process_chapter(chapter_name, common_lines + chapters[chapter_name])
    elif len(chapters) == 0:
        # no chapters; just process all lines
        process_chapter(None, common_lines)
    else:
        # otherwise, process each chapter separately,
        for chapter_name, lines in chapters.items():
            print(f'=== Generating for chapter: {chapter_name} ===')
            # make sure to include the common lines the start
            process_chapter(chapter_name, common_lines + lines)


def process_chapter(chapter_name: str | None, lines: list[Line]):
    '''Processes a single chapter
    Assumes that lines already includes the common lines
    '''
    # generate all compositions
    compositions: list[ExtComposition] = list(process_components(cli_args.ARGS.components, lines))

    # reverse the list so components render in left-to-right order of cli args
    compositions.reverse()

    print("Done generating. Now exporting combined mlt...")

    xml: Element = compositions_to_mlt(compositions)
    fix_and_write_mlt(xml, chapter_name)


def process_components(components: list[str], lines: list[Line]) -> Generator[ExtComposition, None, None]:
    '''Creates a generator that will process each component.
    The generator yields the Composition for that component
    '''
    for component in components:
        match component:
            case macro if macro in configs.COMPONENT_MACROS:
                yield from process_components(configs.COMPONENT_MACROS.get(macro), lines)
            case 'text': yield from gen_text(lines)
            case 'header': yield from gen_header(lines)
            case 'chars': yield from gen_chars(lines)
            case 'chars:p': yield from gen_sided_chars(lines, True)
            case 'chars:e': yield from gen_sided_chars(lines, False)
            case x if x.startswith('char:'): yield from gen_char(lines, x.removeprefix('char:'))
            case x if x.startswith('fill:'): yield from gen_fill(lines, x.removeprefix('fill:'))
            case x if x.startswith('tfill:'): yield from gen_tfill(lines, x.removeprefix('tfill:'))
            case 'groups': yield from gen_groups(lines)
            case x if x.startswith('group:'): yield from gen_group(lines, x.removeprefix('group:'))
            case _: raise ValueError(f'{component} is not a valid component.')


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
    path: Path
    if cli_args.ARGS.output is not None:
        path = Path(cli_args.ARGS.output)
        path = path.with_suffix('.mlt')
    else:
        path = Path(cli_args.ARGS.input)
        path = path.with_suffix('.mlt')

    path = path.with_stem(path.stem + suffix)

    with open(path, 'wb') as outfile:
        xml_string = ElementTree.tostring(xml)
        outfile.write(xml_string)
        print(f'Finished writing output to {path}')

#
# ===  gen_functions ===
# These functions all return generators, even the ones that can only possibly return one Composition
# Means that I don't have to check for None when iterating the result
#


def gen_text(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print("Generating text component")
    yield text_gen.generate(lines)


def gen_header(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print("Generating header overlay component")
    yield header_gen.generate(lines)


def find_all_names(lines: list[Line]) -> list[str]:
    '''Figures out which names appear in the lines.
    Handles wierdness with aliases
    Preserves the order of appearance in the script.
    '''
    # does weird stuff with dict to ensure uniqueness while preserving order
    names: dict[str] = {line.name: None for line in lines if hasattr(line, 'name')}
    names: dict[str] = {configs.follow_alias(name): None for name in names
                        if name in dconfigs.CHARACTERS or name in configs.GLOBAL_ALIASES}
    return list(names)


def gen_chars(lines: list[Line]) -> Generator[ExtComposition, None, None]:
    print("Generating all character components...")
    for name in find_all_names(lines):
        yield from gen_char(lines, name)


def gen_sided_chars(lines: list[Line], is_player: bool) -> Generator[ExtComposition, None, None]:
    '''Generates all characters on the given side, making sure that the speaker is always on the top layer
    '''
    print(f"Generating all {'player' if is_player else 'enemy'} character components...")
    # filter out all names on the wrong side
    names: list[str] = find_all_names(lines)
    names = [name for name in names if CharacterInfo.of_name(name).isPlayer == is_player]

    yield from char_gen.generate_sided(lines, names)


def gen_char(lines: list[Line], character: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating character component for {character}")
    yield char_gen.generate(lines, character)


def gen_fill(lines: list[Line], resource: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating fill with {resource}")
    yield fill_gen.generate(lines, resource)


def gen_tfill(lines: list[Line], resource: str) -> Generator[ExtComposition, None, None]:
    print(f"Generating tfill with {resource}")
    yield tfill_gen.generate(lines, resource)


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
