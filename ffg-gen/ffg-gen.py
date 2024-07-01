#!/usr/bin/env python3

from argparse import ArgumentParser
from xml.etree.ElementTree import Element
from xml.etree import ElementTree
import configs
import dialogueline
import vidgen


def createArgumentParser() -> ArgumentParser:
    parser = ArgumentParser(
        description='Generates mlt files for Touhou-style album videos.')

    parser.add_argument('--config', '-c', type=str,
                        help='path to the config file', default='dialogue-gen.json')
    parser.add_argument('--input', '-i', type=str,
                        help='path to the input dialogue file', default='dialogue.txt')
    parser.add_argument('--output', '-o',  type=str,
                        help='base name of the output file', default='output.mlt')

    subparsers = parser.add_subparsers(help='sub-command help')

    dialogue_parser = subparsers.add_parser(
        'dialogue', help='Generate mlt for a dialogue scene')
    
    dialogue_parser.add_argument(
        'components', nargs='+',
        help='"all" will generate all components. Otherwise, provide one or more options. Options: text, header, chars, char:[name]')

    return parser


def main():
    parser = createArgumentParser()
    configs.ARGS = parser.parse_args()

    configs.loadConfigJson(configs.ARGS.config)

    dialogueLines = None
    with open(configs.ARGS.input) as inputFile:
        dialogueLines = dialogueline.parseDialogueFile(inputFile)

    xml: Element = vidgen.processDialogueLines(dialogueLines)

    with open(configs.ARGS.output, 'wb') as outfile:
        xml_string = ElementTree.tostring(xml)
        outfile.write(xml_string)


if __name__ == "__main__":
    main()
