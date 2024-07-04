#!/usr/bin/env python3

from argparse import ArgumentParser
import configs
import dialogue_gen


def createArgumentParser() -> ArgumentParser:
    parentparser = ArgumentParser(add_help=False)

    parentparser.add_argument(
        '--config', '-c', type=str, default='dialogue-gen.json',
        help='path to the config file')
    parentparser.add_argument(
        '--input', '-i', type=str, default='dialogue.txt',
        help='path to the input dialogue file')
    parentparser.add_argument(
        '--output', '-o',  type=str, default='output.mlt',
        help='base name of the output file')
    parentparser.add_argument(
        '--debug', '-d', action='store_const', const=True, default=False,
        help='causes the program to throw on error instead of just printing and skipping')
    parentparser.add_argument(
        '--no-duration-fix', action='store_const', const=True, default=False, dest='no_duration_fix',
        help='Do not run the duration fix on the resulting mlt. This will mostly likely cause the keyframes to be broken, so no idea why you would enable this.')

    parser = ArgumentParser(
        description='Generates mlt files for Touhou-style album videos.', parents=[parentparser])
    subparsers = parser.add_subparsers(help='the type of scene to generate', required=True)

    dialogue_gen.attach_subparser_to(subparsers, [parentparser])

    return parser


def main():
    parser = createArgumentParser()
    configs.ARGS = parser.parse_args()

    configs.ARGS.func()


if __name__ == "__main__":
    main()
