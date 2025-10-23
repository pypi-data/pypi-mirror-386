def exponent(dic: dict) -> str:
    return "Decimal.exp(" + dic["operators"][0] + ")"


def natural_log(dic: dict) -> str:
    return "Decimal.ln(" + dic["operators"][0] + ")"


def log(dic: dict) -> str:
    if "logbase" in dic:
        return "Decimal.ln(" + dic["operators"][0] + ") / Decimal.ln(" + dic["logbase"] + ")"
    else:
        return natural_log(dic["operators"][0])


def sin(dic: dict) -> str:
    return "sin(" + dic["operators"][0] + ")"


def cos(dic: dict) -> str:
    return "cos(" + dic["operators"][0] + ")"


def tan(dic: dict) -> str:
    return "tan(" + dic["operators"][0] + ")"


def sec(dic: dict) -> str:
    return "1 / cos(" + dic["operators"][0] + ")"


def csc(dic: dict) -> str:
    return "1 / sin(" + dic["operators"][0] + ")"


def cot(dic: dict) -> str:
    return "1 / tan(" + dic["operators"][0] + ")"


def sinh(dic: dict) -> str:
    return "math.sinh(" + dic["operators"][0] + ")"


def cosh(dic: dict) -> str:
    return "math.cosh(" + dic["operators"][0] + ")"


def tanh(dic: dict) -> str:
    return "math.tanh(" + dic["operators"][0] + ")"


def sech(dic: dict) -> str:
    return "1 / math.cosh(" + dic["operators"][0] + ")"


def csch(dic: dict) -> str:
    return "1 / math.sinh(" + dic["operators"][0] + ")"


def coth(dic: dict) -> str:
    return "1 / math.tanh(" + dic["operators"][0] + ")"


def arcsin(dic: dict) -> str:
    return "math.asin(" + dic["operators"][0] + ")"


def arccos(dic: dict) -> str:
    return "math.acos(" + dic["operators"][0] + ")"


def arctan(dic: dict) -> str:
    return "math.atan(" + dic["operators"][0] + ")"


def arcsec(dic: dict) -> str:
    return "math.acos(1 / " + dic["operators"][0] + ")"


def arccsc(dic: dict) -> str:
    return "math.asin(1 / " + dic["operators"][0] + ")"


def arccot(dic: dict) -> str:
    return "math.atan(1 / " + dic["operators"][0] + ")"


def arcsinh(dic: dict) -> str:
    return "math.asinh(" + dic["operators"][0] + ")"


def arccosh(dic: dict) -> str:
    return "math.acosh(" + dic["operators"][0] + ")"


def arctanh(dic: dict) -> str:
    return "math.atanh(" + dic["operators"][0] + ")"


def arcsech(dic: dict) -> str:
    return "math.acosh(1 / " + dic["operators"][0] + ")"


def arccsch(dic: dict) -> str:
    return "math.asinh(1 / " + dic["operators"][0] + ")"


def arccoth(dic: dict) -> str:
    return "math.atanh(1 / " + dic["operators"][0] + ")"
