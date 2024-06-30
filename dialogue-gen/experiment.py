from vidpy import Clip, Composition
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, XML
from mlt_fix import makeXmlEditable

def generateTextFilter(text, geometry, color="#ffffff", bgcolor="0x00000000", olcolor="0x00000000", outline=1, halign="center", valign="middle", pad=0, font="Sans", size=1080, style="normal", weight=400) -> dict:
    return {
        'argument': text,
        'geometry': geometry,
        'family': font,
        'size': size,
        'weight': weight,
        'style': style,
        'fgcolour': color,
        'bgcolour': bgcolor,
        'olcolour': olcolor,
        'outline': outline,
        'pad': pad,
        'halign': halign,
        'valign': valign,
    }


def main():
    tenmu_header: dict = generateTextFilter(
        '天梦', '581 784 350 42 1', size=28, weight=500, olcolor='#763090', halign='left', font='MF KeKe (Noncommercial)')
    fujioki_header: dict = generateTextFilter(
        '不如归', '581 784 350 42 1', size=28, weight=500, olcolor='#a9b7cc', halign='left', font='MF KeKe (Noncommercial)')

    clips = [
        Clip('color:#00000000').set_duration(5).fx('dynamictext', tenmu_header),
        Clip('color:#00000000').set_duration(5).fx('dynamictext', fujioki_header),
        Clip('color:#00000000').set_duration(5).fx('dynamictext', tenmu_header),
        Clip('color:#00000000').set_duration(5).fx('dynamictext', fujioki_header),
    ]

    dialogue_line = Composition(clips, singletrack=True, width=1920, height=1080, fps=30)

    xml: str = dialogue_line.xml()
    fixedXml: Element = makeXmlEditable(XML(xml))

    with open('output.mlt', 'wb') as outfile:
        xml_string = ElementTree.tostring(fixedXml)
        outfile.write(xml_string)

    

if __name__ == "__main__":
    main()