from argparse import ArgumentParser
import json
import config
import parsed


def createArgumentParser() -> ArgumentParser:
    parser = ArgumentParser(description='Generate .')
    parser.add_argument('--config', '-c', type=str,
                        help='path to the config file', default='dialogue-gen.json')
    parser.add_argument('--input', '-i', type=str,
                        help='path to the input dialogue file', default='dialogue.txt')
    parser.add_argument('--output', '-o',  type=str,
                        help='base name of the output file', default='output.mlt')
    return parser


def main():
    parser = createArgumentParser()
    config.ARGS = parser.parse_args()

    with open(config.ARGS.config) as configFile:
        config.CONFIG_JSON = json.load(configFile)

    with open(config.ARGS.input) as inputFile:
        dialogueLines = parsed.parseDialogueFile(inputFile)
        print(dialogueLines)


    


if __name__ == "__main__":
    main()
