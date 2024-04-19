import datetime
import json
import re
from typing import Dict, List
from xml.etree import ElementTree

import xmlschema
from json2xml import json2xml

from config import INCOMING_XML_SCHEMA_PATH, DOCUMENT_INFO_PATH

"""
xml fields to json fields
"""
keys_dict = {
    "Name": "first_name",
    "Surname": "second_name",
    "IdOksm": "citizenship_id",
    "IssueDate": "passport_begda",
    "DocOrganization": "passport_org_code",
    "SubdivisionCode": "passport_org_code",
    "DocNumber": "passport_number",
    "DocSeries": "passport_series",
    "Snils": "snils",
    "IdGender": "dict_sex_id",
    "Birthday": "birthday",
    "Birthplace": "motherland",
    "Phone": "tel_mobile",
    "Email": "email",

}


def compare_document_id(id: int) -> int:
    """
    :param id: passport_type_id from incoming json
    :return: Id from dict_document_type_cls.json
    """
    return id + 100000


def convert_key(key):
    """
    :param key: key name in json data
    :return: key according to XML field name
    """
    return keys_dict.get(key, key)


def get_document_info(id: int) -> Dict:
    """
    :param id: document Id in dict_document_type_cls.json
    :return: dict with appropriate document type information
    """
    with open(DOCUMENT_INFO_PATH, "r", encoding='utf-8') as file:
        documents = json.load(file)
        for doc in documents:
            if doc["Id"] == id:
                return doc


def generate_document_fields(entrant_data: dict, fields: List[Dict]) -> dict | None:
    """
    :param entrant_data: dict with data from incoming json (example: App_info.json)
    :param fields: document fields from dict_document_type_cls.json
    :return: dict with document data
    """
    document_fields = {}
    for field in fields:
        name = field["xml_name"]
        data = entrant_data.get(convert_key(name))
        if data is None and field["not_null"]:
            raise Exception(f"Cant get {name} field !")
        if data:
            document_fields[name] = data
    return document_fields


def get_addresses_info(entrant_data):
    # TODO: create IsRegistration parameter logic
    # TODO: IdRegion, City - ???
    pattern = "^address_txt\d+"
    addresses = []
    is_address = lambda x: re.fullmatch(pattern, x)
    address_fields = list(filter(is_address, entrant_data.keys()))
    for i in range(1, len(address_fields) + 1):
        full_addr = entrant_data.get(f"address_txt{i}")
        if not full_addr:
            break
        address = {"Address": {
            "IsRegistration": True,
            "FullAddr": full_addr,
            "IdRegion": 1,
            "City": "From_kladr"
        }
        }
        addresses.append(address)
    return addresses


def format_data(entrant_data: dict):
    """
    formats data for subsequent recording in xml
    :param entrant_data:
    :return:formated dict
    """

    # TODO: add FreeEducationReason
    # TODO: use pydantic model instead of template(data)
    # Model().model_dump(mode='python') - from model to dict

    document_id = compare_document_id(entrant_data["passport_type_id"])
    document_info = get_document_info(document_id)
    document_fields = document_info["FieldsDescription"]["fields"]
    fields = generate_document_fields(entrant_data, document_fields)  # getting filled documents fields
    addresses = get_addresses_info(entrant_data)
    data = {
        "AddEntrant": {
            "Identification": {
                "IdDocumentType": document_id,
                "DocName": document_info["Name"],
                "DocSeries": entrant_data.get(convert_key("DocSeries")),
                "DocNumber": entrant_data.get(convert_key("DocNumber")),  # ???
                "DocOrganization": entrant_data.get(convert_key("DocOrganization")),
                "Fields": fields
            },
            "IdGender": entrant_data.get(convert_key("IdGender")),
            "Birthplace": entrant_data.get(convert_key("Birthplace")),
            "Phone": entrant_data.get(convert_key("Phone")),
            "Email": entrant_data.get(convert_key("Email")),
            "IdOksm": entrant_data.get(convert_key("IdOksm")),
            "FreeEducationReason": {
                "IdFreeEducationReason": 1,
                "IdOksmFreeEducationReason": 1
            },
            "AddressList": addresses
        }
    }
    snils = entrant_data.get(convert_key("Snils"))
    if snils:
        data["AddEntrant"]["Snils"] = snils

    day, month, year = list(map(int, entrant_data.get(convert_key("IssueDate")).split(".")))
    data["AddEntrant"]["Identification"]["IssueDate"] = datetime.date(year, month, day).strftime("%Y-%m-%d")

    day, month, year = list(map(int, entrant_data.get(convert_key("Birthday")).split(".")))
    data["AddEntrant"]["Birthday"] = datetime.date(year, month, day).strftime("%Y-%m-%d")

    return data


def entrant_data_to_xml(entrant_data: dict, validate=False):
    """
    :param entrant_data:  dict with entrant data from incoming json
    :param path_to_xsd: path to xml schema file
    :return: xml string
    """
    data_to_convert = format_data(entrant_data)
    data = json2xml.Json2xml(data_to_convert, attr_type=False, item_wrap=False, wrapper="EntrantChoice").to_xml()
    if validate:
        try:
            with open(INCOMING_XML_SCHEMA_PATH, encoding='utf-8') as file:
                my_xsd = file.read()
            schema = xmlschema.XMLSchema(my_xsd)
            xml = ElementTree.fromstring(data)
            xmlschema.validate(xml, schema=schema)
        except Exception as e:
            raise Exception(f"Not valid output xml: {e}")

    return data
