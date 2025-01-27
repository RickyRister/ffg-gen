from vidpy.utils import Frame


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


def richTextFilterArgs(text: str, geometry: str, font: str, fontSize: int, color: str = '#ffffff',
                       align: str = "left") -> dict:
    """
    Generates the args for the rich text filter. Use with 'qtext' filter

    Args:
        text: The text in the textbox
        geometry: The geometry of the textbox
        font: The font
        fontSize: The font size
        color: The font color. White by default
        align: The text alignment
    """
    return {
        'argument': 'text',
        'geometry': geometry,
        'html': generateHtml(text, font, fontSize, color, align),
        'pixel_ratio': 1,
        'overflow-y': 1,
        'bgcolour': '#00000000'
    }


HTML = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" /><style type="text/css">
p, li { white-space: pre-wrap; }
hr { height: 1px; border-width: 0; }
li.unchecked::marker { content: "\2610"; }
li.checked::marker { content: "\2612"; }
</style></head><body>
<p align="{ALIGN}" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'{FONT}'; font-size:{SIZE}pt; color:{COLOR};">{TEXT}</span></p></body></html>
"""


def generateHtml(text: str, font: str, fontSize: int, color: str = '#ffffff', align: str = "left") -> str:
    """Generates the html for the rich text filter
    """
    # replace newlines with <br/> so that they show up as newlines in html
    text = text.replace('\n', '<br/>')

    return HTML.replace("{FONT}", font) \
        .replace("{SIZE}", str(fontSize)) \
        .replace("{COLOR}", color) \
        .replace("{TEXT}", text) \
        .replace("{ALIGN}", str(align))


def dropTextFilterArgs(resource: str, end: Frame) -> dict:
    """Generates the args for a mask filter to create the drop text effect. Use with 'mask_start' filter
    """
    return {
        'filter': 'shape',
        "filter.mix": f'0=0;{end}=100',
        "filter.resource": resource,
        "filter.use_luminance": 1,
        "filter.use_mix": 1
    }


def affineFilterArgs(rect: str, halign="center", valign="middle", distort=0) -> dict:
    """Generates the args for the transform filter. use with 'affine' filter

    Args:
        rect: The rect field in the filter. This includes timestamps and geometry
        distort: 1 to use distort
    """
    return {
        'background': 'color:#00000000',
        'transition.fill': '1',
        'transition.distort': distort,
        'transition.rect': rect,
        'transition.valign': halign,
        'transition.halign': valign,
    }


def brightnessFilterArgs(level: str) -> dict:
    """Generates the args for the brightness filter. use with 'brightness' filter

    Args:
        level: The level field in the filter. This includes timestamps and value
    """

    return {
        'level': level
    }


def opacityFilterArgs(alpha: str) -> dict:
    """Generates the args for the opacity filter. use with 'brightness' filter.
    mlt_fix will handle converting this to a shotcut fade-in if able

    Args:
        alpha: The alpha/opacity field in the filter. This includes timestamps and value
    """

    return {
        'alpha': alpha,
    }


def eqToStereoFilterArgs(fov: float, yaw=0, roll=0, amount=100) -> dict:
    '''Generates the args for the 360 Equirectangular to Stereographic filter.
    This is really only intended to map a ribbon into a circular loading bar.

    Use with 'frei0r.bigsh0t_eq_to_stereo' filter.

    Args:
        fov: controls zoom of circle
        yaw: controls rotation of circle
        roll: also controls rotation of circle
        amount: also controls zoom of circle
    '''
    return {
        'fov': fov,
        'yaw': yaw,
        'pitch': -90,
        'roll': roll,
        'amount': amount,
        'interpolation': 0
    }


def cropFilterArgs(rect: str) -> dict:
    '''Generates the args for the Crop: Rectangle filter.

    Use with 'qtcrop' filter.

    Args:
        rect: geometry of the crop
    '''
    return {
        'rect': rect,
        'circle': 0,
        'color': '#00000000',
        'radius': 0,
        'disable': 0
    }


def gaussianBlurFilterArgs(amount: float, blur_alpha: bool = True) -> dict:
    """
    Generates the args for the Blur: Gaussian filter

    Use with the 'avfilter.gblur' filter

    Args:
        amount: percent amount of blur
        blur_alpha: whether Blur Alpha is checked
    """
    return {
        'av.sigma': amount,
        'av.sigmaV': amount,
        'av.planes': '0xf' if blur_alpha else '0x7'
    }
