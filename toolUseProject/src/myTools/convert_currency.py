import requests
from langchain_core.tools import tool


SUPPORTED_CURRENCIES = {
    "CNY": "人民币",
    "USD": "美元",
    "EUR": "欧元",
    "GBP": "英镑",
    "JPY": "日元",
    "HKD": "港币",
}

API_URL = "https://api.frankfurter.dev/v2/rate"


@tool
def convert_currency(amount: float, from_curr: str, to_curr: str) -> str:
    """货币转换工具。

    支持主要货币之间按最新可用汇率进行转换。

    Args:
        amount: 金额数值
        from_curr: 源货币代码（CNY/USD/EUR/GBP/JPY/HKD）
        to_curr: 目标货币代码（CNY/USD/EUR/GBP/JPY/HKD）

    Returns:
        转换结果字符串
    """
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    if from_curr not in SUPPORTED_CURRENCIES:
        supported = ", ".join(SUPPORTED_CURRENCIES)
        return f"不支持的源货币：{from_curr}。支持的货币：{supported}"

    if to_curr not in SUPPORTED_CURRENCIES:
        supported = ", ".join(SUPPORTED_CURRENCIES)
        return f"不支持的目标货币：{to_curr}。支持的货币：{supported}"

    if from_curr == to_curr:
        return f"{amount:.2f} {SUPPORTED_CURRENCIES[from_curr]}（{from_curr}）= {amount:.2f} {SUPPORTED_CURRENCIES[to_curr]}（{to_curr}）"

    try:
        response = requests.get(
            f"{API_URL}/{from_curr}/{to_curr}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"汇率服务请求失败：{exc}"

    rate = data.get("rate")
    quote_date = data.get("date")
    if rate is None or quote_date is None:
        return "未获取到最新汇率数据，请稍后重试。"

    result_amount = amount * rate
    from_name = SUPPORTED_CURRENCIES[from_curr]
    to_name = SUPPORTED_CURRENCIES[to_curr]

    return (
        f"{amount:.2f} {from_name}（{from_curr}）= "
        f"{result_amount:.2f} {to_name}（{to_curr}）"
        f"，汇率 {rate:.6f}，报价日期 {quote_date}"
    )
