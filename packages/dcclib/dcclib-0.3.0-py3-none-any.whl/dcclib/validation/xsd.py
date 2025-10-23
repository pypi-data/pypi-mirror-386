import os
from enum import Enum

from lxml import etree

from ..constants import NAMESPACES
from ..constructible import Constructible
from .errors import XmlError
from .results import XsdValidationResult
from .validatable import Validatable

SCHEMA_FOLDER = os.path.join(os.path.dirname(__file__), "schema", "dcc")


def get_schema_path(version: str):
    return os.path.join(SCHEMA_FOLDER, f"{version}.xsd")


class SchemaVersion(Enum):
    """
    Enum to represent the different versions of the DCC schema.
    """

    v2_1_0 = get_schema_path("v2.1.0")
    v2_1_1 = get_schema_path("v2.1.1")
    v2_2_0 = get_schema_path("v2.2.0")
    v2_3_0 = get_schema_path("v2.3.0")
    v2_4_0 = get_schema_path("v2.4.0")
    v3_0_0 = get_schema_path("v3.0.0")
    v3_1_0 = get_schema_path("v3.1.0")
    v3_1_1 = get_schema_path("v3.1.1")
    v3_1_2 = get_schema_path("v3.1.2")
    v3_2_0 = get_schema_path("v3.2.0")
    v3_2_1 = get_schema_path("v3.2.1")
    v3_3_0 = get_schema_path("v3.3.0")
    latest = v3_3_0


SCHEMA_VERSIONS = [version.name for version in SchemaVersion]


def detect_schema_version(tree: etree.Element) -> SchemaVersion:
    """
    Detect the schema version of an XML file.
    :param tree: the DCC XML tree
    :return: the detected schema version
    """
    version = tree.xpath(
        "/dcc:digitalCalibrationCertificate/@schemaVersion",
        namespaces=NAMESPACES,
    )

    if not version:
        raise ValueError("Could not detect schema version in XML file.")

    version = f"v{version[0].replace('.', '_')}"

    if version not in SCHEMA_VERSIONS:
        raise ValueError(f"Schema version {version} not supported.")

    return SchemaVersion[version]


class XsdValidator(Constructible, Validatable):
    """
    Class to validate XML files against a schema.
    """

    schema_path: str
    parser: etree.XMLParser
    xsd_schema: etree.XMLSchema

    def __init__(self, xmlschema_doc: etree.Element, parser: etree.XMLParser):
        """
        Create an XsdValidator.
        :param xmlschema_doc: the XML schema document
        :param parser: the XML parser
        """
        self.parser = parser
        self.xsd_schema = etree.XMLSchema(xmlschema_doc) if xmlschema_doc is not None else None

    @classmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create an XsdValidator from an XML schema tree.
        :param tree: the XML schema tree
        :returns: the XsdValidator
        """
        parser = etree.XMLParser()
        return cls(tree, parser)

    @classmethod
    def from_file(cls, schema_path: str):
        """
        Create an XsdValidator from a file path.
        :param schema_path: the path to the XSD schema file
        :returns: the XsdValidator
        :raises: FileNotFoundError if the schema file does not exist
        """
        if not os.path.isfile(schema_path):
            raise FileNotFoundError(f"Could not find schema file to validate with: {schema_path}")

        parser = etree.XMLParser()
        xmlschema_doc = etree.parse(schema_path, parser)
        return cls(xmlschema_doc, parser)

    @classmethod
    def from_str(cls, schema_content: str):
        """
        Create an XsdValidator from a string.
        :param schema_content: the content of the XSD schema
        :returns: the XsdValidator
        """
        parser = etree.XMLParser()
        xmlschema_doc = etree.XML(schema_content.encode("utf-8"), parser)
        return cls(xmlschema_doc, parser)

    @classmethod
    def from_version(cls, version: SchemaVersion):
        """
        Create an XsdValidator from a SchemaVersion.
        :param version: the SchemaVersion
        :returns: the XsdValidator
        """
        return cls.from_file(version.value)

    @classmethod
    def from_auto_detection(cls):
        """
        Create an XsdValidator by auto-detecting the schema version.
        :returns: the XsdValidator
        """
        return cls(None, etree.XMLParser())

    def validate_tree(self, tree: etree.Element) -> XsdValidationResult:
        """
        Validate an XML tree against an XSD schema.
        :param tree: the XML tree to validate
        :return: the validation result
        """

        # auto-detect schema version if not set
        if not self.xsd_schema:
            version = detect_schema_version(tree)
            self.xsd_schema = etree.XMLSchema(etree.parse(version.value))

        if not self.xsd_schema.validate(tree):
            return XsdValidationResult(False, [XmlError(error) for error in self.xsd_schema.error_log])

        return XsdValidationResult(True)

    def validate_file(self, xml_path: str) -> XsdValidationResult:
        """
        Validate an XML file against an XSD schema.
        :param xml_path: the path to the XML file
        :return: the validation result
        """
        with open(xml_path, encoding="utf-8") as f:
            xml_content = f.read()
        return self.validate_str(xml_content)

    def validate_str(self, xml_content: str) -> XsdValidationResult:
        """
        Validate an XML file against an XSD schema.
        :param xml_content: the XML string to validate
        :return: the validation result
        """
        try:
            xml_tree = etree.fromstring(xml_content.encode("utf-8"), self.parser)
        except etree.XMLSyntaxError:
            return XsdValidationResult(False, [XmlError(error) for error in self.parser.error_log])

        return self.validate_tree(xml_tree)
