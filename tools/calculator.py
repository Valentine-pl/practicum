# tools/calculator.py
"""
Calculator tool using SymPy for mathematical operations
"""

from typing import Dict, Any
import sympy as sp

from config import DEFAULT_PRECISION, DEFAULT_CALC_MODE


def get_calculator_tool_spec() -> Dict[str, Any]:
    """Return tool specification for Bedrock Converse API"""
    return {
        "toolSpec": {
            "name": "calculator",
            "description": "Advanced calculator for precise mathematical operations. Use this for any calculations instead of doing them yourself.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to calculate (e.g., '2 + 2 * 3', 'sin(pi/2)', 'sqrt(16)')"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["evaluate", "solve"],
                            "description": "Mode: 'evaluate' to calculate, 'solve' to solve equation (default: evaluate)"
                        },
                        "precision": {
                            "type": "integer",
                            "description": f"Number of decimal places (default: {DEFAULT_PRECISION})"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    }


def execute_calculator(
    expression: str,
    mode: str = DEFAULT_CALC_MODE,
    precision: int = DEFAULT_PRECISION
) -> Dict[str, Any]:
    """
    Execute calculator operation
    
    Args:
        expression: Mathematical expression
        mode: 'evaluate' or 'solve'
        precision: Decimal places
        
    Returns:
        Dict with status and result
    """
    try:
        # Parse expression
        expr_str = expression.replace("^", "**")
        expr = sp.sympify(expr_str, evaluate=True)
        
        # Substitute constants
        if expr.has(sp.pi) or expr.has(sp.E):
            expr = expr.subs({
                sp.pi: sp.N(sp.pi, 50),
                sp.E: sp.N(sp.E, 50)
            })
        
        # Execute based on mode
        if mode == "solve":
            if not isinstance(expr, sp.Equality):
                expr = sp.Eq(expr, 0)
            
            variables = list(expr.free_symbols)
            if not variables:
                return {
                    "status": "error",
                    "error": "No variables found to solve"
                }
            
            solution = sp.solve(expr, variables[0])
            
            if isinstance(solution, (list, tuple)):
                result = ", ".join([str(s.evalf(precision)) for s in solution])
            else:
                result = str(solution.evalf(precision))
            
            operation = "solve"
        
        else:  # evaluate
            result_expr = sp.N(expr, precision)
            
            if hasattr(result_expr, "is_integer") and result_expr.is_integer:
                result = str(int(result_expr))
            else:
                result = str(float(result_expr))
            
            operation = "evaluate"
        
        return {
            "status": "success",
            "operation": operation,
            "expression": expression,
            "result": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "expression": expression
        }