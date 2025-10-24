import os
from typing import Dict, Any

import requests
from mcp.server import FastMCP
from requests import RequestException

mcp=FastMCP("Weather")

@mcp.tool()
def current_weather(city:str) -> Dict[str,Any]:
    """
    根据输入城市，查询当前天气
    """
    api_key = os.getenv("SENIVERSE_API_KEY")
    if not api_key:
        raise ValueError("SENIVERSE_API_KEY environment variable is required!")
    try:
        weather_response = requests.get(
            url="https://api.seniverse.com/v3/weather/now.json",
            params={
                "key":api_key,
                "location":city,
                "language":"zh-Hans",
                "unit":"c"
            }
        )
        # 检查 HTTP 请求是否成功，如果请求失败（返回错误状态码），会主动抛出异常
        weather_response.raise_for_status()
        data = weather_response.json()
        results = data["results"]
        if not results:
            return {"error":f"Could not find the weather data for city:{city}"}
        return results[0]
    except RequestException as e:
        error_message = f"Weather API error:{e}"
        # 4xx/5xx的错误类型包含response
        if hasattr(e,'response') and e.response is not None:
            error_data = e.response.json()
            if 'message' in error_data:
                error_message = f"Weather API error: {error_data['message']}"
        return {"error":error_message}


