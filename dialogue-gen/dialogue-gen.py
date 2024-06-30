from argparse import ArgumentParser
import json
import configs
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
    configs.ARGS = parser.parse_args()

    configs.loadConfigJson(configs.ARGS.config)

    dialogueLines = None
    with open(configs.ARGS.input) as inputFile:
        dialogueLines = parsed.parseDialogueFile(inputFile)

    print(dialogueLines)    
    


if __name__ == "__main__":
    main()
