def addition(dic: dict) -> str:
    lst = dic["operators"]
    str = lst[0]
    for el in lst[1:]:
        str += "+" + el
    return str


def subtract(dic: dict) -> str:
    lst = dic["operators"]
    str = lst[0]
    for el in lst[1:]:
        str += "-" + el
    return str


def division(dic: dict) -> str:
    lst = dic["operators"]
    str = lst[0]
    for el in lst[1:]:
        str += "/" + el
    return str


def multiplication(dic: dict) -> str:
    lst = dic["operators"]
    s = lst[0]
    for el in lst[1:]:
        s += "*" + el
    return s


def sqrt(dic: dict) -> str:
    return "Decimal.sqrt(" + dic["operators"][0] + ")"


def power(dic: dict) -> str:
    lst = dic["operators"]
    return lst[0] + "**" + lst[1]


def equal(dic: dict) -> str:
    lst = dic["operators"]
    return lst[0] + "=" + lst[1]
