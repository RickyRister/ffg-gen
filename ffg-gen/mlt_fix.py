import re
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import cli_args
from vidpy_extension.ext_composition import ExtComposition, compositions_to_mlt


def createPropertyElement(property: str, value: str) -> Element:
    """Creates xml Element for <property name="{property}">{value}</property>
    """
    element = Element('property', {'name': property})
    element.text = value
    return element


def fix_and_write_mlt(compositions: list[ExtComposition], file_suffix: str = None):
    '''One-stop shop that takes care of both fixing and exporting the mlt

    Args:
        compositions: a list of ExtCompositions to export to an mlt
        file_suffix: if you want the filename stem to have a suffix
    '''
    # generate initial mlt and fix it
    xml: Element = compositions_to_mlt(compositions)
    fixed_xml: Element = fix_mlt(xml)

    # figure out the output path
    path: Path
    if cli_args.ARGS.output is not None:
        path = Path(cli_args.ARGS.output)
        path = path.with_suffix('.mlt')
    else:
        input_file_name = Path(cli_args.ARGS.input).name
        path = Path(input_file_name)
        path = path.with_suffix('.mlt')

    suffix: str = '' if file_suffix is None else '_' + file_suffix
    path = path.with_stem(path.stem + suffix)

    # write the xml
    with open(path, 'wb') as outfile:
        xml_string = ElementTree.tostring(fixed_xml)
        outfile.write(xml_string)
        print(f'Finished writing output to {path}')


def fix_mlt(xml: Element) -> Element:
    """Edits the xml generated by vidpy to make it work in shotcut
    """

    xml = make_mlt_editable(xml)
    xml = fix_filters(xml)

    xml = fix_affine_out(xml)

    return xml


def make_mlt_editable(xml: Element) -> Element:
    tractor_element: Element = xml.find('.//tractor')
    tractor_element.append(createPropertyElement('shotcut', '1'))

    return xml


def fix_filters(xml: Element) -> Element:
    """Add required shotcut-exclusive tags to filters
    """

    # we need a reference to the parent producer element for each filter element,
    # since certain filter fixes require info contained in the parent
    parent_producers: list[Element] = xml.findall('.//filter/..')

    for parent_producer in parent_producers:
        for filter_element in parent_producer.findall('.//filter'):
            fix_filter_element(filter_element, parent_producer)

    return xml


def fix_filter_element(filter_element: Element, parent_producer: Element):
    '''Add required shotcut-exclusive tags to the filter element.
    '''
    mlt_service: Element = filter_element.find("./property[@name='mlt_service']").text
    match mlt_service:
        case 'dynamictext':
            filter_element.append(createPropertyElement('shotcut:filter', 'dynamicText'))
            filter_element.append(createPropertyElement('shotcut:usePointSize', '1'))
            filter_element.append(createPropertyElement(
                'shotcut:pointSize', filter_element.find("./property[@name='size']").text))
        case 'qtext':
            filter_element.append(createPropertyElement('shotcut:filter', 'richText'))
        case 'mask_start':
            filter_element.append(createPropertyElement('shotcut:filter', 'maskFromFile'))
        case 'affine':
            filter_element.append(createPropertyElement('shotcut:filter', 'affineSizePosition'))
        case 'brightness':
            handle_possible_fades(filter_element, parent_producer)
        case 'frei0r.bigsh0t_eq_to_stereo':
            filter_element.append(createPropertyElement('shotcut:filter', 'bigsh0t_eq_to_stereo'))
        case 'qtcrop':
            filter_element.append(createPropertyElement('shotcut:filter', 'cropRectangle'))
        case 'avfilter.gblur':
            filter_element.append(createPropertyElement('shotcut:filter', 'blur_gaussian_av'))


def handle_possible_fades(brightness_filter: Element, parent_producer: Element):
    """Possibly adds the appropriate fade in/out shotcut filter tag to the known brightness filter.
    We add both fade in and fade outs
    """

    alpha = brightness_filter.find("./property[@name='alpha']")
    if alpha is not None:
        # we assume that all timestamps that we care about are given as frames,
        # since we specifically made it so our program converts everything to frames
        pattern = re.compile(r'(?P<begin>\d+)=(?P<initial>\d);(?P<end>\d+)=(?P<final>\d)')
        matches: re.Match = pattern.match(alpha.text)

        if matches:
            begin, initial, end, final = matches.groups()

            # if a keyframe begins at frame 0 and goes 0 -> 1, then it's definitely a fade-in
            if begin == '0' and initial == '0' and final == '1':
                brightness_filter.append(createPropertyElement(
                    'shotcut:filter', 'fadeInBrightness'))
                brightness_filter.append(createPropertyElement('shotcut:animIn', end))
                return

            # If a keyframes goes 1 -> 0 and ends at the clip's end, then it's definitely a fade-out
            elif end == parent_producer.get('out') and initial == '1' and final == '0':
                animOut = str(int(end) - int(begin))
                brightness_filter.append(createPropertyElement(
                    'shotcut:filter', 'fadeOutBrightness'))
                brightness_filter.append(createPropertyElement('shotcut:animOut', animOut))
                return

        # fallthrough if didn't meet requirements for fade in or fade out
        # no idea what the heck this is, so just add opacity filter and leave it at that
        brightness_filter.append(createPropertyElement('shotcut:filter', 'brightnessOpacity'))
        brightness_filter.append(createPropertyElement('opacity', alpha.text))


def fix_affine_out(xml: Element) -> Element:
    """Copies the out timestamp of the parent producer to any affine filters
    """

    # find all parent nodes of filter nodes
    for producer in xml.findall(".//filter/.."):
        out: str = producer.get('out')

        # loop through all filters nodes of the parent node
        for filter_element in producer.findall('./filter'):

            # replace 'out' if it's an affine filter
            if filter_element.find("./property[@name='mlt_service']").text == 'affine':
                filter_element.set('out', out)

    return xml
