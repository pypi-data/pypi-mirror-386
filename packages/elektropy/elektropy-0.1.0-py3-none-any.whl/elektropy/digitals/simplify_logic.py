import re
import sympy as sp
from sympy.logic.boolalg import simplify_logic as sp_simplify_logic, And, Or, Not, Xor, BooleanTrue, BooleanFalse

_VAR_RE = r"[A-Za-z_]\w*"  # multi-letter names allowed: A, B1, X_out

def _infer_variables(expr: str):
    # find identifiers not immediately followed by '(' -> plain symbols
    # (keeps it simple; adjust if you later add function-like tokens)
    toks = set(re.findall(rf"\b{_VAR_RE}\b", expr))
    # remove known words if you ever add them (True/False etc.)
    return sorted(toks)

def digital_to_sympy(expr: str, variables=None):
    """
    Convert digital notation to a SymPy boolean expression.
    Digital operators:
      * = AND, + = OR, ' = NOT (postfix), ~ = XOR (infix)
    """
    s = expr.replace(" ", "")

    # 1) A'  -> ~(A)
    s = re.sub(rf"({_VAR_RE})'", r"~(\1)", s)

    # 2) XOR:  ~  ->  ^  (SymPy's XOR)
    s = s.replace("~", "^")

    # 3) AND/OR
    s = s.replace("*", "&").replace("+", "|")

    # 4) constants 0/1 (optional)
    s = re.sub(r"\b0\b", "False", s)
    s = re.sub(r"\b1\b", "True", s)

    # Prepare boolean symbols
    if variables is None:
        variables = _infer_variables(expr)
    symmap = {name: sp.symbols(name, boolean=True) for name in variables}

    # Sympify safely
    sympy_expr = sp.sympify(s, locals=symmap, evaluate=True)
    return sympy_expr

def sympy_to_digital(e) -> str:
    """Render a SymPy boolean expression back to your digital syntax."""
    if e is BooleanTrue:
        return "1"
    if e is BooleanFalse:
        return "0"
    if isinstance(e, sp.Symbol):
        return e.name
    if isinstance(e, Not):
        # postfix NOT: A' ; for compound, use (expr)'
        arg = list(e.args)[0]
        inner = sympy_to_digital(arg)
        if isinstance(arg, sp.Symbol):
            return inner + "'"
        else:
            return f"({inner})'"
    if isinstance(e, And):
        parts = [sympy_to_digital(a) for a in e.args]
        return "*".join(_maybe_paren(a, for_op="AND") for a in parts)
    if isinstance(e, Or):
        parts = [sympy_to_digital(a) for a in e.args]
        return "+".join(_maybe_paren(a, for_op="OR") for a in parts)
    if isinstance(e, Xor):
        parts = [sympy_to_digital(a) for a in e.args]
        return "~".join(_maybe_paren(a, for_op="XOR") for a in parts)
    # Fallback to string (rare)
    return str(e)

def _maybe_paren(s: str, for_op: str) -> str:
    # If s contains lower-precedence separators than current op, parenthesize.
    # Precedence (high→low): NOT (postfix), AND(*), XOR(~), OR(+)
    has_plus = "+" in s
    has_tilde = "~" in s
    has_star = "*" in s
    if for_op == "AND":
        # if child is OR or XOR, add parens
        if has_plus or has_tilde:
            return f"({s})"
    elif for_op == "XOR":
        # if child is OR, add parens
        if has_plus:
            return f"({s})"
    elif for_op == "OR":
        # OR is lowest; no need to parenthesize children
        return s
    return s

def simplify_logic(expr: str, *, form: str = "auto", return_sympy: bool = False, variables=None):
    """
    Simplify a Boolean expression written in digital notation.
      Operators: * (AND), + (OR), ' (NOT), ~ (XOR)
    Args:
      expr: digital-notation string, e.g. "A*B' + A*B"
      form: "auto" | "dnf" | "cnf"
      return_sympy: if True, return a SymPy object; else return digital string
      variables: optional list of variable names (to control symbol set/order)
    """
    e = digital_to_sympy(expr, variables=variables)

    if form in ("dnf", "cnf"):
        es = sp_simplify_logic(e, form=form)  # canonical forms
    else:
        es = sp_simplify_logic(e)             # general simplification

    return es if return_sympy else sympy_to_digital(es)