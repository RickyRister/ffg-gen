from functools import partial
from vidpy import Clip, Composition
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, XML
from mlt_fix import makeXmlEditable
from filters import textFilterArgs, richTextFilterArgs, dropTextFilterArgs



def main():
    tenmu_header: dict = textFilterArgs(
        '天梦', '581 784 350 42 1', size=28, olcolor='#763090', halign='left', font='MF KeKe (Noncommercial)')
    fujioki_header: dict = textFilterArgs(
        '不如归', '581 784 350 42 1', size=28, olcolor='#a9b7cc', halign='left', font='MF KeKe (Noncommercial)')
    
    richText = partial(richTextFilterArgs, geometry='576 830 768 159 1', font='Stylish', fontSize=30)

    clips = [
        Clip('color:#00000000').set_duration(5).fx('qtext', richText("bird")).fx('mask_start', dropTextFilterArgs('droptextmask.png')).fx('dynamictext', tenmu_header),
        Clip('color:#00000000').set_duration(5).fx('qtext', richText("bird?")).fx('mask_start', dropTextFilterArgs('droptextmask.png')).fx('dynamictext', fujioki_header),
        Clip('color:#00000000').set_duration(5).fx('qtext', richText("bird's bird bird")).fx('mask_start', dropTextFilterArgs('droptextmask.png')).fx('dynamictext', tenmu_header),
        Clip('color:#00000000').set_duration(5).fx('qtext', richText('"bird" bird bird?')).fx('mask_start', dropTextFilterArgs('droptextmask.png')).fx('dynamictext', fujioki_header),
    ]

    dialogue_line = Composition(clips, singletrack=True, width=1920, height=1080, fps=30)

    xml: str = dialogue_line.xml()
    fixedXml: Element = makeXmlEditable(XML(xml))

    with open('output.mlt', 'wb') as outfile:
        xml_string = ElementTree.tostring(fixedXml)
        outfile.write(xml_string)

    

if __name__ == "__main__":
    main()