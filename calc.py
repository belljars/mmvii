import ast
import operator
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="ast")

# supported operators at the moment :)
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

# variable and function storage
variables = {}
functions = {}

def insert_implicit_multiplication(expr):
    
    # inserts * between number and variable (e.g., 6x -> 6*x)
    
    expr = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expr)  # e.g., 6x, 6(x+1)
    expr = re.sub(r'([a-zA-Z\)])(\d)', r'\1*\2', expr)  # e.g., x6, (x+1)6
    return expr

def eval_expr(expr, local_vars=None):
    
    # safely evaluates a mathematical expression using AST
    expr = expr.replace('^', '**')
    expr = insert_implicit_multiplication(expr)
    try:
        node = ast.parse(expr, mode='eval').body
        return _eval(node, local_vars or {})
    except SyntaxError as e:
        return f"syntax error: {e}"
    except Exception as e:
        return f"evaluation error: {e}"

def _eval(node, local_vars):

    # recursive evaluation of AST nodes
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval(node.left, local_vars)
        right = _eval(node.right, local_vars)
        op_type = type(node.op)
        if op_type in OPS:
            try:
                return OPS[op_type](left, right)
            except Exception as e:
                return f"evaluation error: {e}"
        else:
            return "unsupported operator"
    elif isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand, local_vars)
        op_type = type(node.op)
        if op_type in OPS:
            return OPS[op_type](operand)
        else:
            return "unsupported unary operator"
    elif isinstance(node, ast.Name):
        name = node.id
        if name in local_vars:
            return local_vars[name]
        elif name in variables:
            return variables[name]
        else:
            return f"unknown variable: {name}"
    else:
        return "unsupported expression type"

def handle_assignment(expr):

    # handle variable assignments.
    if '=' in expr and not expr.strip().startswith('f('):
        var, val = expr.split('=', 1)
        var = var.strip()
        val = val.strip()
        result = eval_expr(val)
        if not isinstance(result, str) and isinstance(result, (int, float)):
            variables[var] = result
            return f"{var} = {result}"
        else:
            return result
    return None

def handle_function_definition(expr):
    
    # handle function definitions
    match = re.match(r'([a-zA-Z_]\w*)\((\w+)\)\s*=\s*(.+)', expr)
    if match:
        fname, arg, body = match.groups()
        body = insert_implicit_multiplication(body)
        functions[fname] = (arg, body)
        return f"{fname}({arg}) = {body}"
    return None

def eval_function_call(call):

    # evaluates function calls
    match = re.match(r'([a-zA-Z_]\w*)\(([^)]+)\)', call)
    if match:
        fname, argval = match.groups()
        if fname in functions:
            arg, body = functions[fname]
            try:
                val = eval_expr(argval)
                if isinstance(val, str):
                    return val  # propagate errors from argument evaluation
                local_vars = {arg: val}
                return eval_expr(body, local_vars)
            except Exception as e:
                return f"function Evaluation Error: {e}"
        else:
            return "unknown function"
    return None

def parse_range(range_str):

    # parse range strings like x=5..-5.
    match = re.match(r'(\w+)\s*=\s*(-?\d+)\.\.(-?\d+)', range_str)
    if match:
        var, start, end = match.groups()
        start, end = int(start), int(end)
        step = 1 if end >= start else -1
        return var, list(range(start, end + step, step))
    return None, []

def batch_calculate(exprs):

    # handle comma-separated batch calculations and range evaluations.
    results = []
    exprs = exprs.strip()

    # Range evaluation: f(x) | x=2..-1
    if '|' in exprs:
        func_call, range_part = exprs.split('|', 1)
        func_call = func_call.strip()
        range_part = range_part.strip()
        var, vals = parse_range(range_part)
        if var and vals:
            match = re.match(r'([a-zA-Z_]\w*)\((\w+)\)', func_call)
            if match:
                fname, argname = match.groups()
                if fname in functions:
                    arg, body = functions[fname]
                    for v in vals:
                        local_vars = {arg: v}
                        results.append(eval_expr(body, local_vars))
                    return results
        results.append("error in range syntax")
        return results

    # batch: {f(7), f(4), f(0), f(-3)}
    if exprs.startswith('{') and exprs.endswith('}'):
        exprs = exprs[1:-1]

    for expr in exprs.split(','):
        expr = expr.strip()
        if not expr:
            continue

        # function definition
        func_def = handle_function_definition(expr)
        if func_def:
            results.append(func_def)
            continue

        # variable assignment
        assign = handle_assignment(expr)
        if assign is not None:
            results.append(assign)
            continue

        # function call
        func_call = eval_function_call(expr)
        if func_call is not None:
            results.append(func_call)
            continue

        # plain expression
        results.append(eval_expr(expr))

    return results

def main():
    print("mmvii CLI Calculator /n enter 'q' to quit.")
    while True:
        try:
            inp = input(">> ").strip()
            if inp.lower() in ('q', 'quit', 'exit'):
                break
            results = batch_calculate(inp)
            for res in results:
                print(res)
        except (KeyboardInterrupt, EOFError):
            print("\nquitting")
            break

if __name__ == "__main__":
    main()