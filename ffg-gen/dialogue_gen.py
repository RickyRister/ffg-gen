from argparse import ArgumentParser, _SubParsersAction
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from pathlib import Path
import configs
from dialogueline import DialogueLine, parseDialogueFile
from sysline import SysLine
from generation import text_gen, char_gen


def attach_subparser_to(subparsers: _SubParsersAction, parents) -> None:
    """Adds the command parser for dialogue scene to the subparser"""

    parser: ArgumentParser = subparsers.add_parser(
        'dialogue', help='Generate mlt for a dialogue scene', parents=parents)

    parser.add_argument(
        'components', nargs='+',
        help='"all" will generate all components. Otherwise, provide one or more options. Options: text, header, chars, char:[name]')

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
    try:
        xml: Element = text_gen.generate(lines)
        write_xml(xml, '_text')
    except Exception as e:
        print('Encountered exception while generating text:', e)
        if (configs.ARGS.debug):
            raise e


def gen_header(lines: list[DialogueLine | SysLine]):
    print(f"Generating header component")
    try:
        raise RuntimeError("gen_header not implemented yet")
    except Exception as e:
        print('Encountered exception while generating headers:', e)
        if (configs.ARGS.debug):
            raise e


def gen_chars(lines: list[DialogueLine | SysLine]):
    print(f"Generating all character components...")

    # figure out which characters are in the dialogue
    names: set[str] = {line.character.name for line in lines if isinstance(line, DialogueLine)}

    # call gen_char with all those characters
    for name in names:
        gen_char(lines, name)


def gen_char(lines: list[DialogueLine | SysLine], character: str):
    print(f"Generating character component for {character}")
    try:
        xml: Element = char_gen.generate(lines, character)
        write_xml(xml, f'_{character}')
    except Exception as e:
        print(f'Encountered exception while generating character {character}:', e)
        if (configs.ARGS.debug):
            raise e
