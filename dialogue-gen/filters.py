

def textFilterArgs(text, geometry,
                   color="#ffffff", bgcolor="0x00000000", olcolor="0x00000000",
                   outline=1, halign="left", valign="middle",
                   pad=0, font="Sans", size=1080, style="normal",
                   weight=500) -> dict:
    """
    Generates the args for the simple text filter. Use with 'dynamictext' filter 
    """
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


def richTextFilterArgs(text: str, geometry: str, font: str, fontSize: int, color: str = '#ffffff') -> dict:
    """
    Generates the args for the rich text filter. Use with 'qtext' filter 

    Args:
        text: The text in the textbox. No linebreaks
        geometry: The geometry of the textbox
        font: The font
        fontSize: The font size
        color: The font color. White by default
    """
    return {
        'argument': 'text',
        'geometry': geometry,
        'html': generateHtml(text, font, fontSize, color),
        'pixel_ratio': 1,
        'overflow-y': 1
    }


HTML = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" /><style type="text/css">
p, li { white-space: pre-wrap; }
hr { height: 1px; border-width: 0; }
li.unchecked::marker { content: "\2610"; }
li.checked::marker { content: "\2612"; }
</style></head><body>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'{FONT}'; font-size:{SIZE}pt; color:{COLOR};">{TEXT}</span></p></body></html>
"""


def generateHtml(text: str, font: str, fontSize: int, color: str = '#ffffff') -> str:
    """Generates the html for the rich text filter
    """

    return HTML.replace("{FONT}", font).replace("{SIZE}", str(fontSize)).replace("{COLOR}", color).replace("{TEXT}", text)


def dropTextFilterArgs(resource: str, end: str = '00:00:00.133') -> dict:
    """Generates the args for a mask filter to create the drop text effect. Use with 'mask_start' filter 
    """
    return {
        'filter': 'shape',
        "filter.mix": f'00:00:00.000=0;{end}=100',
        "filter.resource": resource,
        "filter.use_luminance": 1,
        "filter.use_mix": 1
    }
