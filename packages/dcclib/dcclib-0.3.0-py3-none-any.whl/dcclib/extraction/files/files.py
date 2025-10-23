import base64
from dataclasses import dataclass
from enum import Enum

from lxml import etree

from ...constants import NAMESPACES
from ...constructible import Constructible
from ..extractable import Extractable


@dataclass
class StringWithLang:
    """
    Dataclass that represents a string with a language.
    """

    value: str
    lang: str

    def __init__(self, value: str, lang: str):
        self.value = value
        self.lang = lang


@dataclass
class Ring(Enum):
    """
    Enum for that represents the location of the element in the DCC.
    """

    administrative_data = "administrativeData"
    measurement_results = "measurementResults"
    comment = "comment"
    document = "document"


@dataclass
class DCCFile:
    """
    Dataclass that represents a file in the DCC.
    """

    name: list[StringWithLang]
    file_name: str
    mime_type: str
    data_base64: str
    ring: Ring

    def __init__(
        self,
        name: list[StringWithLang],
        file_name: str,
        mime_type: str,
        data_base64: str,
        ring: Ring,
    ):
        self.name = name
        self.file_name = file_name
        self.mime_type = mime_type
        self.data_base64 = data_base64
        self.ring = ring

    def decode_data_base64(self) -> bytes:
        """
        Decode the base64 data.
        @return: the bytes of the decoded data
        """
        return base64.b64decode(self.data_base64)


class FileExtractor(Constructible, Extractable):
    """
    Class to extract files from a DCC XML file.
    """

    def __init__(self, xml_tree: etree.Element):
        self.xml_tree = etree.ElementTree(xml_tree)

    @classmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create a FileExtractor from an etree.Element tree.
        @param tree: the etree.Element tree
        @return: the FileExtractor
        """
        return cls(tree)

    @classmethod
    def from_file(cls, path: str):
        """
        Create a FileExtractor from a DCC XML file path.
        @param path: the path to the DCC XML file
        @return: the FileExtractor
        """
        parser = etree.XMLParser()
        tree = etree.parse(path, parser=parser)
        return cls.from_tree(tree.getroot())

    @classmethod
    def from_str(cls, xml: str):
        """
        Create a FileExtractor from a DCC XML string.
        @param xml: the DCC XML string
        @return: the FileExtractor
        """
        tree = etree.fromstring(xml.encode("utf-8"))
        return cls.from_tree(tree)

    def extract(self) -> list[DCCFile]:
        """
        Extract files from the DCC XML.
        @return: a list of DCCFile objects
        """
        xml_files = self.xml_tree.xpath("//dcc:dataBase64/..", namespaces=NAMESPACES)
        result = []

        for xml_file in xml_files:
            name = xml_file.xpath("dcc:name/dcc:content", namespaces=NAMESPACES)
            file_name = xml_file.xpath("dcc:fileName", namespaces=NAMESPACES)
            mime_type = xml_file.xpath("dcc:mimeType", namespaces=NAMESPACES)
            data_base64 = xml_file.xpath("dcc:dataBase64", namespaces=NAMESPACES)

            element_path = self.xml_tree.getelementpath(xml_file)
            ring = None
            for r in Ring:
                if r.value in element_path:
                    ring = r
                    break

            result.append(
                DCCFile(
                    name=[StringWithLang(n.text, n.attrib.get("lang", "")) for n in name],
                    file_name=file_name[0].text,
                    mime_type=mime_type[0].text,
                    data_base64=data_base64[0].text,
                    ring=ring,
                )
            )

        return result
