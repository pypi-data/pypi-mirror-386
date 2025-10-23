import itertools 
import re

def truth_table(expr, variables) -> str:
    """
    Generate a truth table string for a logic expression using
    + for OR, * for AND, ' for NOT, and ~ for XOR.
    Example:
        print(truth_table("A*B' + C", ["A", "B", "C"]))
    """
    expr = re.sub(r"([A-Za-z0-9_]+)'", r"(not \1)", expr)

    # Replace XOR (~) → ^
    expr = expr.replace("~", "^")

    # Replace AND (*) → and
    expr = expr.replace("*", " and ")

    # Replace OR (+) → or
    expr = expr.replace("+", " or ")

    py_expr = expr

    header = "  ".join(variables) + "  |  " + expr
    lines = [header, "-" * len(header)]

    for combo in itertools.product([0, 1], repeat=len(variables)):
        env = {var: bool(val) for var, val in zip(variables, combo)}

        try:
            result = eval(py_expr, {"__builtins__": None}, env)
        except Exception as e:
            result = f"Error: {e}"

        result_bit = int(bool(result))
        values = "  ".join(str(v) for v in combo)
        lines.append(f"{values}  |  {result_bit}")

    return "\n".join(lines)