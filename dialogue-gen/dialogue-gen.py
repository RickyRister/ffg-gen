from argparse import ArgumentParser
import json
import config


def createArgumentParser() -> ArgumentParser:
    parser = ArgumentParser(description='Generate .')
    parser.add_argument('--configFile', type=str,
                        help='path to the config file', default='dialogue-gen.json')
    parser.add_argument('--outFile',  type=str,
                        help='base name of the output file', default='output.mlt')
    return parser


def main():
    parser = createArgumentParser()
    config.ARGS = parser.parse_args()

    with open(config.ARGS.configFile) as configFile:
        config.CONFIG_JSON = json.load(configFile)
    


if __name__ == "__main__":
    main()
