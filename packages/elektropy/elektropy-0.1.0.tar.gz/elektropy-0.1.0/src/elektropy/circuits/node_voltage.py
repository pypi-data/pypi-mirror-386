import sympy as sp

def node_voltage(equations, variables) -> dict:
    """
    Solve a system of equations using the Node Voltage Method.
    """

    """
    Arguments:
    equations (list): A list of sympy equations representing the circuit.
    variables (list): A list of sympy symbols representing the node voltages to solve for.
    """
    symbols = sp.symbols(variables) 
    expressions = [sp.sympyify(eq) for eq in equations]
    solutions = sp.solve(expressions, symbols)

    if not solutions: 
        raise ValueError("No solution found for the given equations.")
    
    result = {str(var): float(solutions[0][var]) for var in symbols}

    return result