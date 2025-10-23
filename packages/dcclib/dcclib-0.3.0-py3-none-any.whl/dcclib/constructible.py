from abc import ABC, abstractmethod

from lxml import etree


class Constructible(ABC):  # pragma: no cover
    """
    Abstract base class for classes that can be constructed from a string, file path, or tree structure.
    """

    @classmethod
    @abstractmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create an instance from a tree structure.
        @param tree: the tree structure
        @return: an instance of the class
        """
        pass

    @classmethod
    @abstractmethod
    def from_file(cls, path: str):
        """
        Create an instance from a file path.
        @param path: the path to the file
        @return: an instance of the class
        """
        pass

    @classmethod
    @abstractmethod
    def from_str(cls, data: str):
        """
        Create an instance from a string.
        @param data: the string representation
        @return: an instance of the class
        """
        pass
