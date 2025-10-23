from decimal import Decimal


def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("A factorial of a negative number is not allowed!")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


# sinus function with taylor algorithm
def sin(x: Decimal, iterations: int = 10) -> Decimal:
    result = Decimal(0)

    for k in range(iterations):
        term = ((-1) ** k) * (x ** (1 + 2 * k)) / factorial(1 + 2 * k)
        result += term
    return result


def cos(x: Decimal, iterations: int = 10) -> Decimal:
    return sin(90 - x, iterations)


def tan(x: Decimal, iterations: int = 10) -> Decimal:
    return sin(x, iterations) / cos(x, iterations)
