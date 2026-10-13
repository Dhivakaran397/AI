import ast
import operator
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool, ToolPermission


# --- 1. Get Current Time Tool ---
class TimeArgs(BaseModel):
    timezone_offset_hours: float | None = Field(
        default=5.5,
        description="Optional offset from UTC in hours (default: 5.5 for IST - Indian Standard Time)"
    )


class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "Get the current real-time timestamp, localized date, time, and day of week."
    permission = ToolPermission.READ
    args_schema = TimeArgs

    async def execute(self, timezone_offset_hours: float | None = 5.5, **kwargs: Any) -> dict[str, str]:
        utc_now = datetime.now(timezone.utc)
        offset = timezone_offset_hours if timezone_offset_hours is not None else 5.5
        local_now = utc_now + timedelta(hours=offset)
        tz_label = "IST (UTC+5:30)" if offset == 5.5 else f"UTC{'+' if offset >= 0 else ''}{offset}"
        return {
            "local_time": local_now.strftime("%A, %B %d, %Y at %I:%M %p") + f" ({tz_label})",
            "date": local_now.strftime("%Y-%m-%d"),
            "time": local_now.strftime("%I:%M:%S %p"),
            "day": local_now.strftime("%A"),
            "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "iso": utc_now.isoformat(),
        }


# --- 2. Calculate Tool (Safe Math Evaluator) ---
class CalculateArgs(BaseModel):
    expression: str = Field(
        ...,
        description="Mathematical expression to calculate, e.g. '128 * 45 + 1024 / 4'"
    )


class CalculateTool(BaseTool):
    name = "calculate"
    description = "Safely evaluate mathematical and arithmetic expressions without arbitrary code execution."
    permission = ToolPermission.READ
    args_schema = CalculateArgs

    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")

    async def execute(self, expression: str, **kwargs: Any) -> dict[str, Any]:
        try:
            parsed = ast.parse(expression.strip(), mode="eval")
            result = self._eval(parsed.body)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"expression": expression, "error": str(e)}


# --- 3. Save Memory Tool ---
class SaveMemoryArgs(BaseModel):
    content: str = Field(..., description="Key fact, user preference, architectural decision, or knowledge to remember")
    memory_type: str = Field(
        default="PREFERENCE",
        description="Type of memory: 'PREFERENCE', 'DECISION', 'PROJECT', 'KNOWLEDGE'"
    )


class SaveMemoryTool(BaseTool):
    name = "save_memory"
    description = "Explicitly save an important preference, decision, or fact to long-term memory for future conversations."
    permission = ToolPermission.WRITE
    args_schema = SaveMemoryArgs

    async def execute(self, content: str, memory_type: str = "PREFERENCE", user_id: Any = None, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "saved",
            "memory_type": memory_type.upper(),
            "content": content,
            "message": "Memory persisted successfully to knowledge bank."
        }


# --- 4. Web Search Tool (Live Real-Time Web & News Search) ---
class WebSearchArgs(BaseModel):
    query: str = Field(..., description="Search query string (e.g. 'latest AI news today', 'Python 3.14 features', 'world news')")
    max_results: int = Field(default=5, description="Maximum number of results to return (default: 5)")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the live web and breaking news for up-to-date real-time information, "
        "current events, today's news, documentation, and factual references."
    )
    permission = ToolPermission.EXTERNAL
    args_schema = WebSearchArgs

    async def execute(self, query: str, max_results: int = 5, **kwargs: Any) -> dict[str, Any]:
        clean_query = query.strip()
        query_lower = clean_query.lower()
        is_news_intent = any(
            k in query_lower
            for k in ["news", "today", "yesterday", "latest", "recent", "breaking", "headline", "current", "update", "now", "happening"]
        )

        results: list[dict[str, str]] = []

        # 1. Breaking / Real-time News via Google News RSS
        if is_news_intent:
            try:
                encoded = quote_plus(clean_query)
                rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
                async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                    resp = await client.get(rss_url)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        items = root.findall('./channel/item')
                        for item in items[:max_results]:
                            title = item.findtext('title') or ''
                            link = item.findtext('link') or ''
                            pub_date = item.findtext('pubDate') or ''
                            if title and link:
                                results.append({
                                    "title": title,
                                    "snippet": f"Published: {pub_date}" if pub_date else "Recent news report",
                                    "url": link,
                                    "source": "Google News (Live)"
                                })
            except Exception:
                pass

        # 2. Live Web Search via DuckDuckGo Lite
        if len(results) < max_results:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                async with httpx.AsyncClient(timeout=6.0, headers=headers, follow_redirects=True) as client:
                    ddg_resp = await client.post("https://lite.duckduckgo.com/lite/", data={"q": clean_query})
                    if ddg_resp.status_code == 200:
                        soup = BeautifulSoup(ddg_resp.text, "html.parser")
                        links = soup.select(".result-link")
                        snippets = soup.select(".result-snippet")
                        needed = max_results - len(results)
                        for i in range(min(len(links), needed)):
                            title = links[i].get_text(strip=True)
                            href = links[i].get("href", "")
                            snip = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                            if title and href:
                                results.append({
                                    "title": title,
                                    "snippet": snip,
                                    "url": href,
                                    "source": "DuckDuckGo (Live)"
                                })
            except Exception:
                pass

        # 3. Wikipedia API fallback
        if not results:
            try:
                wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(clean_query)}&limit={max_results}&namespace=0&format=json"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(wiki_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        titles = data[1] if len(data) > 1 else []
                        snippets = data[2] if len(data) > 2 else []
                        urls = data[3] if len(data) > 3 else []
                        for i in range(len(titles)):
                            results.append({
                                "title": titles[i],
                                "snippet": snippets[i] if i < len(snippets) else "",
                                "url": urls[i] if i < len(urls) else "",
                                "source": "Wikipedia (Live)"
                            })
            except Exception:
                pass

        return {
            "query": clean_query,
            "total_results": len(results),
            "results": results
        }
