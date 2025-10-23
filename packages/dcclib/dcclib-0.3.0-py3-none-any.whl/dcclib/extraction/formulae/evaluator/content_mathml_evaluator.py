import re

from .basic_arithmetics import (
    addition,
    division,
    equal,
    multiplication,
    power,
    sqrt,
    subtract,
)
from .elementary_functions import (
    arccos,
    arccosh,
    arccot,
    arccoth,
    arccsc,
    arccsch,
    arcsec,
    arcsech,
    arcsin,
    arcsinh,
    arctan,
    arctanh,
    cos,
    cosh,
    cot,
    coth,
    csc,
    csch,
    exponent,
    log,
    natural_log,
    sec,
    sech,
    sin,
    sinh,
    tan,
    tanh,
)
from .sequences_series import product, sum

RX_SECURE = "[A-z0-9]+"


def get_localname(txt: str) -> str:
    return txt.split("}")[-1]


methods = {
    # "csymbol": csymbol,
    # Basic Arithmetic
    "plus": addition,
    "minus": subtract,
    "divide": division,
    "times": multiplication,
    "eq": equal,
    "root": sqrt,
    "power": power,
    # Basic Functions
    "exp": exponent,
    "ln": natural_log,
    "log": log,
    # Common trigonomic functions
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "sec": sec,
    "csc": csc,
    "cot": cot,
    # Common hyperbolic functions
    "sinh": sinh,
    "cosh": cosh,
    "tanh": tanh,
    "sech": sech,
    "csch": csch,
    "coth": coth,
    # Common inverses of trigonomic functions
    "arcsin": arcsin,
    "arccos": arccos,
    "arctan": arctan,
    "arcsec": arcsec,
    "arccsc": arccsc,
    "arccot": arccot,
    # Common inverses of hyperbolic functions
    "arcsinh": arcsinh,
    "arccosh": arccosh,
    "arctanh": arctanh,
    "arcsech": arcsech,
    "arccsch": arccsch,
    "arccoth": arccoth,
    # Sequence Series
    "sum": sum,
    "product": product,
}


def iter_applies(apply, nsmap):
    kind_applies = apply.findall("./ml:apply", namespaces=nsmap)
    results = []
    if kind_applies:
        for kind_apply in kind_applies:
            results += ["(" + str(iter_applies(kind_apply, nsmap)) + ")"]

    operand = get_localname(apply[0].tag)
    dic = {}
    operators = []

    for node in apply[1:]:
        localname = get_localname(node.tag)
        if localname in ["ci", "cn"]:
            if re.match(RX_SECURE, node.text):
                operators += [node.text]
        elif localname == "apply":
            pass
        else:
            if re.match(RX_SECURE, node.getchildren()[0].text):
                dic[localname] = node.getchildren()[0].text

    if operand not in methods:
        print("Operand is not implemented!")
    else:
        if results != []:
            operators += results

        dic["operators"] = operators
        result = methods[operand](dic)
        return result


def convert_formula(apply, nsmap):
    return iter_applies(apply, nsmap)
