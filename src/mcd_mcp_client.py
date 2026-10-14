"""麦当劳 MCP streamable HTTP 客户端。

仅封装本项目用到的最小能力：建立会话并调用指定 Tool。
Token 从环境变量 MCD_MCP_TOKEN 读取，严禁硬编码或写入仓库。
"""
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "https://mcp.mcd.cn"


def _token() -> str:
    token = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if not token:
        raise SystemExit("请先设置环境变量 MCD_MCP_TOKEN（从 open.mcd.cn 控制台申请）")
    return token


def _extract_payload(result) -> list:
    """把 tools/call 的结果统一转成可 JSON 化的列表。

    MCP 返回的 content 可能是 text（内嵌 JSON 字符串）或 structuredContent，
    两种形态都兼容，上层只关心最终的数据结构。
    """
    text_parts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    if result.structuredContent:
        data = result.structuredContent
    elif text_parts:
        data = json.loads("".join(text_parts))
    else:
        data = []
    return data if isinstance(data, list) else [data]


async def call_tool(name: str, arguments: dict | None = None) -> list:
    """调用麦当劳 MCP 的一个 Tool，返回归一化后的数据列表。"""
    headers = {"Authorization": f"Bearer {_token()}"}
    async with streamablehttp_client(MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments or {})
            return _extract_payload(result)


async def list_nutrition_foods() -> list:
    """获取餐品营养信息列表（本项目核心数据源）。"""
    return await call_tool("list-nutrition-foods")
