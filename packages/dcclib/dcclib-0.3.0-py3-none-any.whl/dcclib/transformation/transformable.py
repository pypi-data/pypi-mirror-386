from abc import ABC, abstractmethod

from lxml import etree


class Transformable(ABC):  # pragma: no cover
    """
    Abstract base class for classes that can perform transformations on a string, file path, or tree structure.
    """

    @abstractmethod
    def transform_tree(self, xml_tree: etree.Element) -> str:
        """
        Transform an XML tree.
        @param xml_tree: XML tree to transform
        @returns: Transformed XML string
        """
        pass

    @abstractmethod
    def transform_file(self, xml_path: str) -> str:
        """
        Transform an XML file.
        @param xml_path: Path to the XML file to transform
        @returns: Transformed XML string
        """
        pass

    @abstractmethod
    def transform_str(self, xml_content: str) -> str:
        """
        Transform an XML.
        @param xml_content: XML string to transform
        @returns: Transformed XML string
        """
        pass
