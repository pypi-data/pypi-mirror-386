import os

from lxml import etree
from saxonche import PySaxonProcessor

from dcclib.constructible import Constructible
from dcclib.transformation.transformable import Transformable


class XsltProcessor(Constructible, Transformable):
    """
    Processor for XSLT transformations.
    """

    def __init__(self, xslt: str, cwd: str = os.getcwd()):
        """
        Initializes the XSLT processor with the given XSLT string.
        :param xslt: XSLT string
        :param cwd: Current working directory
        """

        self.proc = PySaxonProcessor(license=False)
        self.proc.set_cwd(cwd)
        self.xslt_proc = self.proc.new_xslt30_processor()
        self.xslt_executable = self.xslt_proc.compile_stylesheet(stylesheet_text=xslt, encoding="UTF-8")

    @classmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create an XsltProcessor from an etree.Element tree.
        :param tree: the etree.Element tree
        :returns: the XsltProcessor
        """
        return cls(etree.tostring(tree, pretty_print=True).decode("utf-8"))

    @classmethod
    def from_str(cls, string: str):
        """
        Create an XsltProcessor from a string.
        :param string: the content of the XSLT schema
        :returns: the XsltProcessor
        """
        return cls(string)

    @classmethod
    def from_file(cls, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"XSLT file not found: {path}")

        return cls(open(path).read())

    def transform_tree(self, xml_tree: etree.Element) -> str:
        """
        Transforms an XML tree with the xslt string.
        :param xml_tree: XML tree to transform
        :returns: Transformed XML string
        """
        return self.transform_str(etree.tostring(xml_tree, pretty_print=True).decode("utf-8"))

    def transform_file(self, xml_path: str) -> str:
        """
        Transforms an XML file with the xslt string.
        :param xml_path: Path to the XML file to transform
        :returns: Transformed XML string
        """
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"XML file not found: {xml_path}")

        document = self.proc.parse_xml(xml_file_name=xml_path)

        return self.xslt_executable.transform_to_string(
            xdm_node=document,
        )

    def transform_str(self, xml_content: str) -> str:
        """
        Transforms a xml with the xslt string.
        :param xml_content: XML string to transform
        :returns: Transformed XML string
        """
        document = self.proc.parse_xml(xml_text=xml_content)

        return self.xslt_executable.transform_to_string(
            xdm_node=document,
        )
