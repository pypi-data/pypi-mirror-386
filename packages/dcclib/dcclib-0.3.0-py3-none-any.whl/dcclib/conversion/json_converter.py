import json

import xmlschema
from lxml import etree

from ..constructible import Constructible
from ..validation.xsd import detect_schema_version
from .convertible import Convertible


class JSONConverter(Constructible, Convertible):
    """
    JSONConverter class that converts DCC XML to JSON whilst being schema-aware.
    """

    def __init__(self, xml_doc: xmlschema.XmlDocument):
        """
        Constructor for JSONConverter class.
        @param xml_doc: XmlDocument to be converted to JSON.
        """
        self.xml_doc = xml_doc

    @classmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create a JSONConverter from an etree.Element tree.
        @param tree: the etree.Element tree
        @return: the JSONConverter
        """
        schema_version = detect_schema_version(tree)
        schema = xmlschema.XMLSchema(schema_version.value)

        # allow=none disables loading of external schemas
        return cls(xml_doc=xmlschema.XmlDocument(tree, validation="skip", defuse="always", allow="none", schema=schema))

    @classmethod
    def from_file(cls, path: str):
        """
        Create a JSONConverter from a DCC XML file path.
        @param path: the path to the DCC XML file
        @return: the JSONConverter
        """
        tree = etree.parse(path)
        return cls.from_tree(tree)

    @classmethod
    def from_str(cls, xml: str):
        """
        Create a JSONConverter from a DCC XML string.
        @param xml: the DCC XML string
        @return: the JSONConverter
        """
        tree = etree.fromstring(xml.encode("utf-8"))
        return cls.from_tree(tree)

    def convert(self) -> str:
        """
        Convert the DCC XML to JSON.
        @return: the JSON representation of the DCC XML
        """
        return json.dumps(obj=self.xml_doc.schema.to_dict(self.xml_doc, preserve_root=True), indent=2)
