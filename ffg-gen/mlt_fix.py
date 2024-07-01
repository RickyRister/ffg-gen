from xml.etree.ElementTree import Element
from xml.etree import ElementTree
import re
import configs


def createPropertyElement(property: str, value: str) -> Element:
    """Creates xml Element for <property name="{property}">{value}</property>
    """
    element = Element('property', {'name': property})
    element.text = value
    return element


def fix_mlt(xml: Element) -> Element:
    """Edits the xml generated by vidpy to make it work in shotcut
    """

    xml = make_mlt_editable(xml)
    xml = fix_filters(xml)
    xml = fix_out_timestamps(xml)
    xml = fix_affine_out(xml)

    return xml


def make_mlt_editable(xml: Element) -> Element:
    tractor_element: Element = xml.find('.//tractor')
    tractor_element.append(createPropertyElement('shotcut', '1'))

    return xml


def fix_filters(xml: Element) -> Element:
    """Add required shotcut-exclusive tags to filters
    """

    for filter_element in xml.findall('.//filter'):
        mlt_service: Element = filter_element.find("./property[@name='mlt_service']").text
        match(mlt_service):
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
                handle_possible_fades(filter_element)

    return xml


def handle_possible_fades(brightness_filter: Element):
    """Possibly adds the appropriate fade in/out shotcut filter tag to the known brightness filter
    """

    alpha = brightness_filter.find("./property[@name='alpha']")
    if alpha is not None:
        pattern = re.compile('00:00:00\.000=(?P<initial>\d);(?P<end>.+)=\d')
        matches: re.Match = pattern.match(alpha.text)

        match (matches.group('initial')):
            case '1':
                brightness_filter.append(createPropertyElement(
                    'shotcut:filter', 'fadeOutBrightness'))
                brightness_filter.append(createPropertyElement(
                    'shotcut:animOut', matches.group('end')))
            case '0':
                brightness_filter.append(createPropertyElement(
                    'shotcut:filter', 'fadeInBrightness'))
                brightness_filter.append(createPropertyElement(
                    'shotcut:animIn', matches.group('end')))


def fix_out_timestamps(xml: Element) -> Element:
    """Replace the out timestamps on each producer with the equivalent timestamp, if known.
    """

    fixes: dict[str, str] = {str(threshold.expectedFrames): threshold.fix
                             for threshold in configs.DURATIONS.thresholds
                             if threshold.expectedFrames is not None and threshold.fix is not None}

    for producer in xml.findall('.//*[@out]'):
        expectedFrames = producer.get('out')
        fix = fixes.get(expectedFrames)

        if fix is None:
            print(f"No fix found for out frame {expectedFrames}")
            continue

        producer.set('out', fix)

    return xml


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
