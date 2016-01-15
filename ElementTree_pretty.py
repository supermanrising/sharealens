from xml.etree import ElementTree
from xml.dom import minidom

# Reference: https://pymotw.com/2/xml/etree/ElementTree/create.html

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")