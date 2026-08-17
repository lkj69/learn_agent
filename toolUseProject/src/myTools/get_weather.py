import requests
from langchain_core.tools import tool


@tool
def get_weather(city: str, dateTime: str) -> str:
    """
    查询指定城市在指定日期的天气。
    :param city: 城市名称，如 "北京"、"Shanghai"、"Tokyo"
    :param dateTime: 日期，格式 YYYY-MM-DD，如 "2026-08-20"
    :return: 该城市当天的天气描述与温度字符串
    """
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "zh"},
        timeout=10,
    ).json()
    if not geo.get("results"):
        return f"找不到城市：{city}"

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    wx = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "start_date": dateTime,
            "end_date": dateTime,
            "timezone": "auto",
        },
        timeout=10,
    ).json()

    try:
        daily = wx["daily"]
        idx = daily["time"].index(dateTime)
        code = daily["weathercode"][idx]
        return (
            f"{dateTime}，{city} 的天气代码是 {code}，"
            "常见代码示例：0=晴，3=多云，61=小雨，95=雷暴。"
            f"最高温 {daily['temperature_2m_max'][idx]}°C，"
            f"最低温 {daily['temperature_2m_min'][idx]}°C，"
            f"降水 {daily['precipitation_sum'][idx]} mm。"
        )
    except (KeyError, ValueError):
        return f"未获取到 {city} 在 {dateTime} 的天气数据。"
