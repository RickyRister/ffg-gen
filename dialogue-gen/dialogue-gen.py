from argparse import ArgumentParser
from xml.etree.ElementTree import Element
from xml.etree import ElementTree 
import configs
import parsing
import vidgen


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
        dialogueLines = parsing.parseDialogueFile(inputFile)

    xml: Element = vidgen.processDialogueLines(dialogueLines)

    with open(configs.ARGS.output, 'wb') as outfile:
        xml_string = ElementTree.tostring(xml)
        outfile.write(xml_string)
    


if __name__ == "__main__":
    main()
