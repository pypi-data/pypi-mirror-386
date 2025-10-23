from dataclasses import dataclass

from .errors import SchematronReport, XmlError


@dataclass
class XsdValidationResult:
    """
    Class to represent the result of an XML validation against a schema.
    """

    is_valid: bool
    errors: list[XmlError]

    def __init__(self, is_valid: bool, errors: list[XmlError] = None):
        if errors is None:
            errors = []
        self.is_valid = is_valid
        self.errors = errors


@dataclass
class SchematronValidationResult:
    """
    Class to represent the result of an XML validation against a schematron file.
    """

    is_valid: bool
    failed_assertions: list[SchematronReport]
    successful_reports: list[SchematronReport]

    def __init__(
        self,
        is_valid: bool,
        failed_assertions: list[SchematronReport] = None,
        successful_reports: list[SchematronReport] = None,
    ):
        if failed_assertions is None:
            failed_assertions = []
        if successful_reports is None:
            successful_reports = []
        self.is_valid = is_valid
        self.failed_assertions = failed_assertions
        self.successful_reports = successful_reports
