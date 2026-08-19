import requests

from ._server import mcp


PRODUCT_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
NEWS_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


def _search_products(keyword: str) -> list[str]:
    response = requests.get(
        PRODUCT_SEARCH_URL,
        params={
            "action": "query",
            "list": "search",
            "format": "json",
            "utf8": 1,
            "srlimit": 5,
            "srsearch": keyword,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "未知条目")
        snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
        page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        results.append(f"【产品/资料】{title}：{snippet}\n链接：{page_url}")
    return results


def _search_news(keyword: str) -> list[str]:
    response = requests.get(
        NEWS_SEARCH_URL,
        params={
            "query": keyword,
            "hitsPerPage": 5,
            "tags": "story",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("hits", []):
        title = item.get("title") or "无标题"
        url = item.get("url") or item.get("story_url") or "无链接"
        author = item.get("author") or "未知作者"
        created_at = item.get("created_at") or "未知时间"
        results.append(f"【新闻】{title}\n作者：{author}，时间：{created_at}\n链接：{url}")
    return results


@mcp.tool()
def search_info(keyword: str, category: str = "all") -> str:
    """搜索各类信息。

    Args:
        keyword: 搜索关键词
        category: 搜索分类，可选 product、news、all

    Returns:
        搜索结果字符串
    """
    category = category.lower()
    if category not in {"product", "news", "all"}:
        return "不支持的搜索分类。支持的分类：product, news, all"

    results = []
    errors = []

    if category in {"product", "all"}:
        try:
            product_results = _search_products(keyword)
            if product_results:
                results.extend(product_results)
        except requests.RequestException as exc:
            errors.append(f"产品搜索请求失败：{exc}")

    if category in {"news", "all"}:
        try:
            news_results = _search_news(keyword)
            if news_results:
                results.extend(news_results)
        except requests.RequestException as exc:
            errors.append(f"新闻搜索请求失败：{exc}")

    if results:
        return "\n\n".join(results)

    if errors:
        return "\n".join(errors)

    return f"未找到关于“{keyword}”的 {category} 信息。"
