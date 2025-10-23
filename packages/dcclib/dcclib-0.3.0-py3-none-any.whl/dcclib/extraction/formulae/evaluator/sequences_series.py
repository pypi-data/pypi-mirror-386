def sum(dic: dict) -> str:
    if "lowlimit" not in dic:
        dic["lowlimit"] = 0

    return (
        "sum("
        + dic["operators"][0]
        + " for "
        + dic["bvar"]
        + " in range("
        + dic["lowlimit"]
        + ", "
        + dic["uplimit"]
        + " + 1))"
    )


def product(dic: dict) -> str:
    if "lowlimit" not in dic:
        dic["lowlimit"] = 0

    return (
        "math.prod("
        + dic["operators"][0]
        + " for "
        + dic["bvar"]
        + " in range("
        + dic["lowlimit"]
        + ", "
        + dic["uplimit"]
        + " + 1))"
    )


def limit(dic: dict) -> str:
    pass
