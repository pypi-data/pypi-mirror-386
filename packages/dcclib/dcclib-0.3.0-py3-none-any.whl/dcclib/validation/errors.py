from dataclasses import dataclass, field

SVRL_NS = {"svrl": "http://purl.oclc.org/dsdl/svrl"}


@dataclass
class XmlError:
    """
    Class to represent an error that occurred during XML validation.
    """

    column: int = field()
    domain: str = field()
    domain_name: str = field()
    level: int = field()
    level_name: str = field()
    line: int = field()
    message: str = field()
    type: str = field()
    type_name: str = field()

    def __init__(self, log_error):
        self.column = log_error.column
        self.domain = log_error.domain
        self.domain_name = log_error.domain_name
        self.level = log_error.level
        self.level_name = log_error.level_name
        self.line = log_error.line
        self.message = log_error.message
        self.path = log_error.path
        self.type = log_error.type
        self.type_name = log_error.type_name


@dataclass
class SchematronReport:
    """
    Class to represent a report from a schematron validation.
    """

    location: str = field()
    role: str = field()
    test: str = field()
    text: str = field()

    def __init__(self, failed_assert):
        self.location = failed_assert.attrib.get("location", "")
        self.role = failed_assert.attrib.get("role", "")
        self.test = failed_assert.attrib.get("test", "")
        text = failed_assert.find("svrl:text", namespaces=SVRL_NS)
        self.text = "\n".join(part.strip() for part in text.text.strip().split("\n")) if text is not None else ""
