import os

from lxml import etree

from ..constructible import Constructible
from ..transformation import XsltProcessor
from .errors import SchematronReport
from .results import SchematronValidationResult
from .validatable import Validatable

CURRENT_DIR = os.path.dirname(__file__)
SVRL_PATH = os.path.join(CURRENT_DIR, "schema", "dcc.svrl")
SVRL_NS = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
SCHXSLT_PATH = os.path.join(CURRENT_DIR, "schema", "schxslt")
SVRL_COMPILE_XSLT_PATH = os.path.join(SCHXSLT_PATH, "compile-for-svrl.xsl")


# TODO: fix usage for svrl and schematron
class SchematronValidator(Constructible, Validatable):
    """
    Class to validate XML files against a schematron file.
    """

    def __init__(self, svrl_content: str):
        """
        Create a SchematronValidator.
        :param svrl_content: the content of the compiled schematron file
        """
        self.xslt_processor = XsltProcessor.from_str(svrl_content)

    @classmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create a SchematronValidator from an etree.Element tree.
        @param tree: the etree.Element tree
        @return: the SchematronValidator
        """
        return cls(compile_schematron_to_svrl(etree.tostring(tree, pretty_print=True).decode("utf-8")))

    @classmethod
    def from_str(cls, schematron_content: str):
        """
        Create a SchematronValidator from a string.
        :param schematron_content: the content of the schematron file
        :returns: the SchematronValidator
        """
        return cls(compile_schematron_to_svrl(schematron_content))

    @classmethod
    def from_file(cls, schematron_path: str):
        """
        Create a SchematronValidator from a file path.
        :param schematron_path: the path to the schematron file
        :returns: the SchematronValidator
        """
        # check if the svrl file exists
        if not os.path.isfile(schematron_path):
            raise FileNotFoundError(f"Could not find schematron file to validate with: {schematron_path}")
        with open(schematron_path, encoding="utf-8") as f:
            schematron_content = f.read()
        return cls(compile_schematron_to_svrl(schematron_content))

    @classmethod
    def for_dcc(cls):
        """
        Create a SchematronValidator for the DCC schematron.
        :returns: the SchematronValidator
        """
        if not os.path.exists(SVRL_PATH):
            raise FileNotFoundError(f"Could not find DCC schematron file: {SVRL_PATH}")
        with open(SVRL_PATH, encoding="utf-8") as f:
            return cls(f.read())

    def validate_tree(self, tree: etree.Element) -> SchematronValidationResult:
        """
        Validate an XML file against a schematron file.
        :param tree: the XML tree to validate
        :returns: the validation result
        """
        return self.validate_str(etree.tostring(tree, pretty_print=True).decode("utf-8"))

    def validate_file(self, xml_path: str) -> SchematronValidationResult:
        """
        Validate an XML file against a schematron file.
        :param xml_path: the path to the XML file to validate
        :returns: the validation result
        """
        with open(xml_path, encoding="utf-8") as f:
            xml = f.read()
        return self.validate_str(xml)

    def validate_str(self, xml_content: str) -> SchematronValidationResult:
        """
        Validate an XML file against a schematron file.
        :param xml_content: the XML string to validate
        :returns: the validation result
        """

        result = self.xslt_processor.transform_str(xml_content)

        err_tree = etree.fromstring(result.encode("utf-8"))
        failed_assertions = err_tree.findall("svrl:failed-assert", namespaces=SVRL_NS)
        successful_reports = err_tree.findall("svrl:successful-report", namespaces=SVRL_NS)

        return SchematronValidationResult(
            len(failed_assertions) == 0,
            [SchematronReport(assertion) for assertion in failed_assertions],
            [SchematronReport(report) for report in successful_reports],
        )


def compile_schematron_to_svrl(schematron: str) -> str:
    """
    Compile a schematron file to a svrl file.
    :param schematron: the schematron content to compile
    """
    if not os.path.exists(SVRL_COMPILE_XSLT_PATH):
        raise FileNotFoundError(f"Could not find schXslt file: {SVRL_COMPILE_XSLT_PATH}")

    with open(SVRL_COMPILE_XSLT_PATH, encoding="utf-8") as f:
        schXslt_content = f.read()

    xslt_processor = XsltProcessor(xslt=schXslt_content, cwd=SCHXSLT_PATH)
    return xslt_processor.transform_str(schematron)
