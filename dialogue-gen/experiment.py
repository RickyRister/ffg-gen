from vidpy import Clip, Composition, Text


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


""" 
'shotcut:filter': 'dynamictext',
        'shotcut:usePointSize': 1,
        'shotcut:animIn': '00:00:00.000',
        'shotcut:animOut': '00:00:00.000',
        'shotcut:pointSize': 28
"""


clip1 = Clip('color:#00000000')
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

stiched = Composition(clips, singletrack=True, width=1920, height=1080, fps=30)
stiched.save_xml('output.mlt')
