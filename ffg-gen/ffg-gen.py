#!/usr/bin/env python3

from argparse import ArgumentParser
from xml.etree.ElementTree import Element
from xml.etree import ElementTree
import configs
import dialogueline
from generation import text_gen
import dialogue_gen


def createArgumentParser() -> ArgumentParser:
    parser = ArgumentParser(
        description='Generates mlt files for Touhou-style album videos.')

    parser.add_argument('--config', '-c', type=str,
                        help='path to the config file', default='dialogue-gen.json')
    parser.add_argument('--input', '-i', type=str,
                        help='path to the input dialogue file', default='dialogue.txt')
    parser.add_argument('--output', '-o',  type=str,
                        help='base name of the output file', default='output.mlt')

    subparsers = parser.add_subparsers(
        help='the type of scene to generate for', required=True)

    dialogue_gen.attach_subparser_to(subparsers)

    return parser


def main():
    parser = createArgumentParser()
    configs.ARGS = parser.parse_args()

    configs.ARGS.func()


if __name__ == "__main__":
    main()
