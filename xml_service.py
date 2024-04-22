from xml.etree import ElementTree

import xmlschema
import xmltodict

from config import OUTPUT_XML_SCHEMA_PATH
from json_service import convert_key


def flatten(d: dict) -> dict:
    flatten_d = dict()

    for k, v in d.items():
        if isinstance(v, dict):
            flatten_d.update(flatten(v))
        else:
            flatten_d[convert_key(k)] = v

    return flatten_d


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
    addresses = dict_data["PackageData"]["SuccessResultList"]["Entrant"].pop("AddressList")
    dict_data = flatten(dict_data)
    cnt = 0
    for address in addresses["Address"]:
        cnt += 1
        dict_data[f"address_registration{cnt}"] = address['IsRegistration']
        dict_data[f"address_txt{cnt}"] = address['FullAddr']
        dict_data[f"address_city{cnt}"] = address['City']
        dict_data[f"address_region{cnt}"] = address['IdRegion']
    return dict_data
