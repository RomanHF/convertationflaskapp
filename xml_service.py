from xml.etree import ElementTree

import xmlschema
import xmltodict
from flatten_json import flatten

from config import OUTPUT_XML_SCHEMA_PATH


def entrant_to_json(xml_data: str, validate=False):
    if validate:
        try:
            with open(OUTPUT_XML_SCHEMA_PATH, encoding='utf-8') as file:
                my_xsd = file.read()
            schema = xmlschema.XMLSchema(my_xsd)
            xml = ElementTree.fromstring(xml_data)
            xmlschema.validate(xml, schema=schema)
        except Exception as e:
            raise Exception(f"Not valid input xml: {e}")
    dict_data = xmltodict.parse(xml_data)
    return flatten(dict_data)
