from langchain_core.tools import tool
import math

@tool
def calculator(expression: str) -> str:
    """执行数学计算
    支持基本运算符（+、-、*、/、**）和常用数学函数
    Args:
    expression: 数学表达式，可以包含：
    - 基本运算：2 + 3, 10 * 5, 100 / 4
    - 幂运算：2 ** 10
    - 函数：sqrt(16), abs(-5), pow(2, 3)
    Returns:
    计算结果或错误信息
    Examples:
    calculator("2 + 3 * 4") 返回 "14"
    calculator("sqrt(16)") 返回 "4.0"
    """
    try:
    # 安全的数学运算环境
        safe_functions = {
        "sqrt": math.sqrt,
        "pow": pow,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "pi": math.pi,
        "e": math.e
        }
        result = eval(expression, {"__builtins__": {}}, safe_functions)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错：{str(e)}\n提示：请检查表达式格式，支持的函数有 sqrt,abs, pow, sin, cos, tan, log)"