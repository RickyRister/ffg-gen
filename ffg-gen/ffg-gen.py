#!/usr/bin/env python3

from argparse import ArgumentParser
import cli_args
from dialogue_gen import dialogue_gen


def createArgumentParser() -> ArgumentParser:
    parentparser = ArgumentParser(add_help=False)

    parentparser.add_argument(
        '--config', '-j', type=str, default='dialogue-gen.json',
        help='path to the config json')
    parentparser.add_argument(
        '--input', '-i', type=str, default='dialogue.txt',
        help='path to the input dialogue file')
    parentparser.add_argument(
        '--output', '-o',  type=str, default=None,
        help='base name of the output file')
    parentparser.add_argument(
        '--bg-color', type=str, default='black', dest='bg_color',
        help='Color of the backing track. Can be a color word or hex. (default black)')

    parser = ArgumentParser(description='Generates mlt files for Touhou-style album videos.',
                            parents=[parentparser])
    subparsers = parser.add_subparsers(help='the type of scene to generate', required=True)

    dialogue_gen.attach_subparser_to(subparsers, [parentparser])

    return parser


def main():
    parser = createArgumentParser()
    cli_args.ARGS = parser.parse_args()

    cli_args.ARGS.func()


if __name__ == "__main__":
    main()
