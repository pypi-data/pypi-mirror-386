from collections.abc import Iterator
from dataclasses import dataclass

from mpmath import mp
from sympy import Expr, lambdify, symbols
from sympy.parsing.sympy_parser import parse_expr


def sub_len(list_with_sublists: list[mp.mpf | list[mp.mpf]]) -> int:
    """
    Get the length of the sublists in a list.
    Mixtures of lists and non-lists are allowed, non-lists are counted as sublists of length 1.
    @param l: the list
    @raise ValueError: if the sublists have different lengths or the list contains empty sublists
    @return: the length of the sublists
    """
    length = 0
    list_length = len(list_with_sublists)

    if list_length == 0:
        return 0

    for i in range(list_length):
        if isinstance(list_with_sublists[i], list):
            sub_length = len(list_with_sublists[i])
            # if length is already set, check if the sublists have the same length
            if 1 <= length != sub_length:
                raise ValueError("Sublists have different lengths.")
            elif sub_length > length:
                length = sub_length
        elif length == 0:
            # non-list found
            length = 1

    # no non-lists found and empty sublists.
    if length == 0:
        raise ValueError("List contains empty sublists.")

    return length


def _generate_variable_combinations(
    bound_variables: set[str], variables: dict[str, mp.mpf | list[mp.mpf]]
) -> Iterator[lambdify]:
    """
    Generate a restricted cartesian product of the variables.
    It is restricted by the indexes of the values in the lists.
    Example:
    A: [0, 100]
    B: 0.5
    C: [25, 75]
    will generate:
    {A: 0, B: 0.5, C: 25}
    {A: 100, B: 0.5, C: 75}

    @param bound_variables: the variables bound in the function
    @param variables: all variables and their values
    @raise ValueError: if the number of values for unbound variables and bound variables are not equal or one
                       of them is not 1
    @return: a generator of variable combinations
    """

    unbound_variables = {k: v for k, v in variables.items() if k not in bound_variables}
    unbound_vars_length = max(sub_len(list(unbound_variables.values())), 1)

    # iterate over all combinations of unbound variables
    for i in range(unbound_vars_length):
        # prepare variables as a dictionary, take appropriate value from list if necessary
        variable_combination = {key: value[i] if isinstance(value, list) else value for key, value in variables.items()}
        yield variable_combination


@dataclass
class DCCFunction:
    """
    Class to represent a DCC function.
    """

    name: str
    expression: any
    variables: dict[str, mp.mpf | list[mp.mpf]]
    bound_variables: set[str]

    def __init__(
        self,
        name: str,
        expression: str,
        variables: dict[str, mp.mpf | list[mp.mpf]],
        bound_variables: set[str],
    ):
        self.name = name
        self.expression = parse_expr(expression)
        self.variables = variables
        self.bound_variables = bound_variables

    @property
    def combinations(self) -> list[lambdify]:
        """
        Get the substitutions for a restricted cartesian product of the variables.
        @return: the lambdified substitutions
        """
        unbound_variables = {k: v for k, v in self.variables.items() if k not in self.bound_variables}
        return [
            lambdify(
                symbols(self.bound_variables),
                self.expression.subs(combination),
                modules="mpmath",
            )
            for combination in _generate_variable_combinations(self.bound_variables, unbound_variables)
        ]

    def evaluate(self, variables: dict[str, mp.mpf | list[mp.mpf]] = None) -> list[mp]:
        if variables is None:
            variables = {}

        results = []
        combined_vars = self.variables | variables
        combined_bvars = {k: v for k, v in combined_vars.items() if k in self.bound_variables}
        combined_unbound_vars = {k: v for k, v in combined_vars.items() if k not in combined_bvars}

        # check that all bound variables are present
        if combined_bvars.keys() != self.bound_variables:
            raise ValueError(
                "Could not evaluate function with given variables."
                f"Missing bound variables: {self.bound_variables.difference(combined_bvars.keys())}"
            )

        combinations = [
            lambdify(
                symbols(tuple(self.bound_variables)),
                self.expression.subs(combination),
                modules="mpmath",
            )
            for combination in _generate_variable_combinations(self.bound_variables, combined_unbound_vars)
        ]
        unbound_vars_length = max(sub_len(list(combined_unbound_vars.values())), 1)
        bvars_length = max(sub_len(list(combined_bvars.values())), 1)
        length = max(unbound_vars_length, bvars_length)

        if unbound_vars_length != 1 and bvars_length != 1 and bvars_length != unbound_vars_length:
            raise ValueError(
                "The number of values for bound variables and unbound variables must be equal or one of them must be 1."
            )

        # incorporate combinations of bound_variables
        for i in range(length):
            # variables are already substituted in the function, only bound variables need to be passed
            calc_vars = {key: value[i] if isinstance(value, list) else value for key, value in combined_bvars.items()}
            res = combinations[i](**calc_vars) if unbound_vars_length > 1 else combinations[0](**calc_vars)

            # check if the expression evaluated to a sympy expression, which means that not all variables were bound
            if isinstance(res, Expr):
                raise ValueError(
                    "Could not evaluate function with given variables."
                    f"Symbols(s) {', '.join(map(str, res.free_symbols))} are not bound to a value."
                )
            else:
                results.append(res)

        return results
