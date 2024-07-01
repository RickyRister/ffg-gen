from argparse import ArgumentParser, _SubParsersAction
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from pathlib import Path
import configs
from dialogueline import DialogueLine, parseDialogueFile
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

    dialogueLines = None
    with open(configs.ARGS.input) as inputFile:
        dialogueLines = parseDialogueFile(inputFile)

    for component in configs.ARGS.components:
        match (str.lower(component)):
            case 'all': gen_all(dialogueLines)
            case 'text': gen_text(dialogueLines)
            case 'header': gen_header(dialogueLines)
            case 'chars': gen_chars(dialogueLines)
            case x if x.startswith('char:'): gen_char(dialogueLines, x.removeprefix('char:'))
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


def gen_all(dialogueLines: list[DialogueLine]):
    gen_text(dialogueLines)
    gen_header(dialogueLines)
    gen_chars(dialogueLines)


def gen_text(dialogueLines: list[DialogueLine]):
    try:
        xml: Element = text_gen.processDialogueLines(dialogueLines)
        write_xml(xml, '_text')
    except Exception as e:
        print('Encountered exception while generating text:', e)
        if (configs.ARGS.debug):
            raise e


def gen_header(dialogueLines: list[DialogueLine]):
    try:
        raise RuntimeError("gen_header not implemented yet")
    except Exception as e:
        print('Encountered exception while generating headers:', e)
        if (configs.ARGS.debug):
            raise e


def gen_chars(dialogueLines: list[DialogueLine]):
    # figure out which characters are in the dialogue
    names = set(map(lambda dl: dl.character.name, dialogueLines))

    # call gen_char with all those characters
    for name in names:
        gen_char(dialogueLines, name)


def gen_char(dialogueLines: list[DialogueLine], character: str):
    try:
        xml: Element = char_gen.generate(dialogueLines, character)
        write_xml(xml, f'_{character}')
    except Exception as e:
        print(f'Encountered exception while generating character {character}:',
              e)
        if (configs.ARGS.debug):
            raise e
