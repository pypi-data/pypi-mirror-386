"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

from mcp.server.fastmcp import FastMCP
import urllib.request
from urllib.error import HTTPError, URLError
import urllib.parse
import json
from pypinyin import lazy_pinyin

# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# Add weather query tool
@mcp.tool()
def get_weather(city: str = "深圳") -> str:
    """Get current weather information for a city using urllib.request (OpenWeatherMap).

    Note: OpenWeatherMap temps are in Kelvin; convert to Celsius.
    """
    try:
        p = "".join(lazy_pinyin(city))
        city = p.lower()
        print(city)
        q = urllib.parse.quote(f"{city},cn")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={q}&appid=24fb0e0396bf67707c01b8b2ca3c98cb"
        req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/3"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")

        if status != 200:
            return f"天气API请求失败，HTTP 状态：{status}，内容：{body}"

        data = json.loads(body)
        cod = data.get("cod")
        if str(cod) != "200":
            return f"获取{city}天气失败：{data.get('message', data)}"

        name = data.get("name", city)
        main = data.get("main", {})
        weather = (data.get("weather") or [{}])[0]

        def k2c(k):
            try:
                return round(k - 273.15, 1)
            except Exception:
                return "未知"

        temp = k2c(main.get("temp"))
        temp_max = k2c(main.get("temp_max"))
        temp_min = k2c(main.get("temp_min"))
        feels = k2c(main.get("feels_like"))
        desc = weather.get("description", "未知")

        info = (
            f"{name}今日天气：\n"
            f"- 当前温度：{temp}°C\n"
            f"- 天气：{desc}\n"
            f"- 最高温度：{temp_max}°C\n"
            f"- 最低温度：{temp_min}°C\n"
            f"- 体感温度：{feels}°C\n"
        )
        return info
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        return f"HTTP error {e.code}: {err_body}"
    except URLError as e:
        return f"Network error: {e.reason}"
    except Exception as e:
        return f"获取天气信息时出现错误：{e}"


def main() -> None:
    mcp.run()
