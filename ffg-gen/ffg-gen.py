from argparse import ArgumentParser
import cli_args
from dialogue_gen import dialogue_gen
from bio_gen import bio_gen
from ending_gen import ending_gen


def createArgumentParser() -> ArgumentParser:
    parentparser = ArgumentParser(add_help=False)

    parentparser.add_argument(
        '--output', '-o',  type=str, default=None,
        help='base name of the output file')
    parentparser.add_argument(
        '--bg-color', type=str, default='black', dest='bg_color',
        help='Color of the backing track. Can be a color word or hex. (default black)')
    parentparser.add_argument(
        '--fill-blanks', action='store_const', const=True, default=False, dest='fill_blanks',
        help='Use transparent clips for waits instead of blanks.')

    parser = ArgumentParser(description='Generates mlt files for Touhou-style album videos.',
                            parents=[parentparser])
    subparsers = parser.add_subparsers(help='the type of scene to generate', required=True)

    dialogue_gen.attach_subparser_to(subparsers, [parentparser])
    bio_gen.attach_subparser_to(subparsers, [parentparser])
    ending_gen.attach_subparser_to(subparsers, [parentparser])

    return parser


def main():
    parser = createArgumentParser()
    cli_args.ARGS = parser.parse_args()

    cli_args.ARGS.func()


if __name__ == "__main__":
    main()
