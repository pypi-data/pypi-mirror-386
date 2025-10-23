from abc import ABC, abstractmethod

from lxml import etree


class Validatable(ABC):  # pragma: no cover
    """
    Abstract base class for classes that can validate a tree structure, file, or
    string representation.
    """

    @abstractmethod
    def validate_tree(self, tree: etree.Element):
        """
        Validate a tree structure.
        @param tree: the tree structure
        """
        pass

    @abstractmethod
    def validate_file(self, xml_path: str):
        """
        Validate a file path.
        @param xml_path: the path to the file
        """
        pass

    @abstractmethod
    def validate_str(self, xml_content: str):
        """
        Validate a string representation.
        @param xml_content: the string representation
        """
        pass
