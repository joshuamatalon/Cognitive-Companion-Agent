import ast
import operator
import pandas as pd
from io import BytesIO

_ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ops:
        return _ops[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ops:
        return _ops[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("Unsupported expression")


def calculator(expr: str) -> str:
    try:
        return f"{expr} = {_eval(ast.parse(expr, mode='eval').body)}"
    except Exception as e:
        return f"Calc error: {e}"


def summarize_csv_bytes(b: bytes, max_rows: int = 5) -> str:
    try:
        df = pd.read_csv(BytesIO(b))
    except Exception as e:
        return f"CSV read error: {e}"
    return (
        f"Columns: {list(df.columns)}\n\n"
        f"Head:\n{df.head(max_rows).to_string()}\n\n"
        f"Describe:\n{df.describe(include='all').transpose().head(10).to_string()}"
    )
