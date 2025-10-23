import sympy as sp

def series_resistance(*resistors) -> float:
    """
    Calculate the total resistance of resistors in series.
    """

    """
    Arguments: resitors (float or int)
    """
    return sum(resistors)

def parallell_resistance(*resistors) -> float:
    """
    Calculate the total resistance of resistors in parallel.
    """

    """
    Arguments: resitors (float or int)
    """
    reciprocal = sum(1 / r for r in resistors)
    return 1 / reciprocal if reciprocal != 0 else float('inf')