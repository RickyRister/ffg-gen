from argparse import ArgumentParser, _SubParsersAction
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, XML
from pathlib import Path
from typing import Callable
from vidpy import Composition
import configs
from dialogueline import DialogueLine, parseDialogueFile
from sysline import SysLine
from generation import text_gen, char_gen
from characterinfo import CharacterInfo
import mlt_fix


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

    for component in configs.ARGS.components:
        match (str.lower(component)):
            case 'all': gen_all(lines)
            case 'text': gen_text(lines)
            case 'header': gen_header(lines)
            case 'chars': gen_chars(lines)
            case x if x.startswith('char:'): gen_char(lines, x.removeprefix('char:'))
            case _: print(f'{component} is not a valid option; skipping')


def wrap_generate(gen_function: Callable[[list], Composition], file_suffix: str, error_msg: str):
    '''Wraps the generate() call to do all the handling stuff'''
    try:
        xml_string: str = gen_function().xml()
        fixed_xml: Element = mlt_fix.fix_mlt(XML(xml_string))
        write_xml(fixed_xml, '_' + file_suffix)
    except Exception as e:
        print(error_msg, e)
        if configs.ARGS.debug:
            raise e
    finally:
        reset_configs()


def write_xml(xml: Element, suffix: str = ''):
    """Writes the xml to a file.
    The suffix is appended to the output name given by the cli args
    """
    path: Path = Path(configs.ARGS.output)
    path = path.with_stem(path.stem + suffix)

    with open(path, 'wb') as outfile:
        xml_string = ElementTree.tostring(xml)
        outfile.write(xml_string)


def gen_all(lines: list[DialogueLine | SysLine]):
    gen_text(lines)
    gen_header(lines)
    gen_chars(lines)


def gen_text(lines: list[DialogueLine | SysLine]):
    print(f"Generating text component")
    wrap_generate(lambda: text_gen.generate(lines), 'text',
                  'Encountered exception while generating text:')


def gen_header(lines: list[DialogueLine | SysLine]):
    print(f"Generating header component")

    def raiser(): raise RuntimeError("gen_header not implemented yet")
    wrap_generate(raiser, 'header',
                  'Encountered exception while generating headers:')


def gen_chars(lines: list[DialogueLine | SysLine]):
    print(f"Generating all character components...")

    # figure out which characters are in the dialogue
    names: set[str] = {line.name for line in lines if hasattr(line, 'name')}

    # call gen_char with all those characters
    for name in names:
        gen_char(lines, name)


def gen_char(lines: list[DialogueLine | SysLine], character: str):
    print(f"Generating character component for {character}")
    wrap_generate(lambda: char_gen.generate(lines, character), f'{character}',
                  f'Encountered exception while generating character {character}:')


def reset_configs():
    '''Resets any global configs that might have gotten altered during a run
    '''
    CharacterInfo.get_cached.cache_clear()
