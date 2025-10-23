import os
import re
import warnings

from lxml import etree
from mpmath import mp

from dcclib.extraction.formulae.evaluator.content_mathml_evaluator import convert_formula

from ...constants import NAMESPACES
from .formula import DCCFunction

# accuracy of numbers
mp.dps = 50


class MLNames:
    MATHML_NS = "http://www.w3.org/1998/Math/MathML"
    MATHML_DECLARE = f"{{{MATHML_NS}}}declare"
    MATHML_APPLY = f"{{{MATHML_NS}}}apply"
    MATHML_CI = f"{{{MATHML_NS}}}ci"
    MATHML_LAMBDA = f"{{{MATHML_NS}}}lambda"
    MATHML_BVAR = f"{{{MATHML_NS}}}bvar"


def extract_vars(apply, tree, nsmap) -> dict[str, mp.mpf | list[mp.mpf]]:
    vars_dict = {}
    vars = apply.findall(".//ml:ci", namespaces=nsmap)

    for var in vars:
        if "xref" in var.attrib:
            # find the element which got the id of the xref
            el = tree.find('.//dcc:*[@id="' + var.attrib["xref"] + '"]', namespaces=nsmap)
            # check if element has a valuexmlList
            value_list = el.find(".//si:valueXMLList", namespaces=nsmap)
            if value_list is not None:
                # get list of elements with blank space seperator
                xml_elements = value_list.text.split(" ")

                number_list: list[mp.mpf] = []
                for xml_element in xml_elements:
                    # convert all elements in list to decimal
                    number_list += [mp.mpf(xml_element)]
                vars_dict[var.text] = number_list
            else:
                value = el.find(".//si:value", namespaces=nsmap)
                vars_dict[var.text] = mp.mpf(value.text)
    return vars_dict


def handle_mathml_fn(fn_node, nsmap) -> (str, str, set[str]):
    if fn_node[0].tag == MLNames.MATHML_CI:
        fn_name = fn_node[0].text
        fn_expression = ""

        bvars = []
        if fn_node[1].tag == MLNames.MATHML_LAMBDA:
            for lambda_el in list(fn_node[1]):
                if lambda_el.tag == MLNames.MATHML_BVAR:
                    if lambda_el[0].tag == MLNames.MATHML_CI:
                        if re.match(r"[A-z0-9]", lambda_el[0].text):
                            bvars += [lambda_el[0].text]
                        else:
                            print("Prohibited characters in variable names!")
                elif lambda_el.tag == MLNames.MATHML_APPLY:
                    fn_expression = convert_formula(lambda_el, nsmap)
        if re.match(r"[A-z0-9]+", fn_name):
            return fn_name, fn_expression, set(bvars)
        else:
            print("Prohibited characters in function name!")


class FormulaExtractor:
    def __init__(self, element: etree.Element):
        self.element = element

    @classmethod
    def from_tree(cls, tree: etree.Element):
        """
        Create a FormulaExtractor from an ElementTree.
        @param tree: the ElementTree
        @return: the FormulaExtractor
        """
        return cls(tree)

    @classmethod
    def from_path(cls, path: str):
        """
        Create a FormulaExtractor from a file path.
        @param path: the path to the file
        @return: the FormulaExtractor
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Could not find file: {path}")

        parser = etree.XMLParser()
        tree = etree.parse(path, parser=parser)
        return cls.from_tree(tree)

    @classmethod
    def from_str(cls, xml: str):
        """
        Create a FormulaExtractor from a string.
        @param xml: the XML string
        @return: the FormulaExtractor
        """
        parser = etree.XMLParser()
        tree = etree.fromstring(xml.encode("utf-8"), parser=parser)
        return cls.from_tree(tree)

    def extract(self) -> list[DCCFunction]:
        """
        Extract formulas from the XML.
        @return: a list of DCCFunction objects
        """
        formulas: list = self.element.findall(".//ml:math", namespaces=NAMESPACES)
        results = []

        for formula in formulas:
            # applies = formula.findall('.//ml:apply', namespaces=nsmap)
            for child in list(formula):
                variables = extract_vars(child, self.element, NAMESPACES)
                match child.tag:
                    # check if it is a declare element or an apply formula
                    case MLNames.MATHML_DECLARE:
                        # check if we want to declare a function
                        if child.attrib["type"] in ["fn", "function"]:
                            # get the result out of handle mathml function
                            fn_name, fn_expression, bvars = handle_mathml_fn(child, NAMESPACES)

                            results.append(DCCFunction(fn_name, fn_expression, variables, bvars))
                    case MLNames.MATHML_APPLY:
                        warnings.warn("MathML apply is not implemented yet!", stacklevel=2)
                        pass
                    case _:
                        warnings.warn("Unknown MathML element!", stacklevel=2)
                        pass

        return results
