"""麦当劳 MCP streamable HTTP 客户端。

仅封装本项目用到的最小能力：建立会话并调用指定 Tool。
Token 从环境变量 MCD_MCP_TOKEN 读取，严禁硬编码或写入仓库。
"""
import json
import os
import re

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "https://mcp.mcd.cn"


def _token() -> str:
    token = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if not token:
        raise SystemExit("请先设置环境变量 MCD_MCP_TOKEN（从 open.mcd.cn 控制台申请）")
    return token


def parse_nutrition_payload(text: str) -> list[dict]:
    """解析 list-nutrition-foods 的返回。

    该 Tool 返回一段说明文字 + 内嵌 JSON，JSON 的 data 字段是伪 CSV：
        [160]{productName,energyKcal,...}:
          猪柳麦满分,null,1288,308,16,16,24,781,213
          ...
    本函数把它解析成标准 dict 列表。
    """
    start = text.find('{"success"')
    if start < 0:
        raise ValueError("响应中未找到 JSON 主体")
    depth, end = 0, start
    for end in range(start, len(text)):
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
            if depth == 0:
                break
    blob = text[start:end + 1]
    body = json.loads(blob)
    if not body.get("success"):
        raise RuntimeError(f"MCP 返回错误: {body.get('code')} {body.get('message')}")
    data = body.get("data") or ""
    lines = [ln.strip() for ln in data.splitlines() if ln.strip()]
    if not lines:
        return []
    header = re.search(r'\{(.+?)\}', lines[0])
    fields = [f.strip() for f in header.group(1).split(",")] if header else []
    items = []
    for ln in lines[1:]:
        cols = ln.split(",")
        row = dict(zip(fields, cols))
        row.pop("nutritionDescription", None)
        items.append(row)
    return items


async def call_tool_raw(name: str, arguments: dict | None = None):
    """调用一个 Tool，返回原始 result（content/structuredContent 原样保留）。"""
    http_client = httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {_token()}"},
        timeout=30.0,
    )
    async with streamable_http_client(MCP_URL, http_client=http_client) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, arguments or {})


async def list_nutrition_foods() -> list[dict]:
    """获取餐品营养信息列表（本项目核心数据源）。"""
    result = await call_tool_raw("list-nutrition-foods")
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    return parse_nutrition_payload("".join(texts))
