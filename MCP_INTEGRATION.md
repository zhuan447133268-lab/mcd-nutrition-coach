# MCP 集成说明

本项目真实调用麦当劳 MCP Server（`https://mcp.mcd.cn`，Streamable HTTP 协议，Bearer Token 鉴权）。

## 使用的麦当劳 MCP Server

| 项目 | 值 |
|---|---|
| Server 地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | `Authorization: Bearer <MCD_MCP_TOKEN>`（Token 从 open.mcd.cn 控制台申请，仅通过环境变量注入，不落库不入仓） |
| 官方文档 | [M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server) |

## 使用的 Tool 与调用流程

### 核心链路（营养搭配必经）

```
用户目标（热量/蛋白质/预算/场景）
        │
        ▼
list-nutrition-foods  ──获取在售餐品营养数据（能量/蛋白质/脂肪/碳水/钠/钙）
        │
        ▼
本地营养引擎（nutrition_engine.py）
  · 字段归一化（FIELD_MAP）
  · 硬约束过滤（热量≤上限、价格≤预算、钠≤上限）
  · 组合搜索 + 评分排序（蛋白质达成度、营养均衡度）
        │
        ▼
输出 3 套候选组合（明细、小计、达标标注、取舍说明）
```

### 可选联动链路（省钱/下单场景）

| Tool | 用途 | 触发时机 |
|---|---|---|
| `query-nearby-stores` | 定位附近门店 | 用户需要到店/外送时 |
| `query-meals` | 查当前门店可售菜单与价格 | 需要实时价格或确认在售时 |
| `query-store-coupons` / `available-coupons` | 查可用优惠券 | 用户要求"最省钱"时 |
| `calculate-price` | 用优惠券复算应付金额 | 选定组合后给出实付价 |
| `create-order` | 创建订单 | 用户明确说"就这套，下单"（需二次确认） |

> 点餐/下单类 Tool 均为可选增强，本项目核心价值（营养搭配）只依赖 `list-nutrition-foods` 一个 Tool，即使下单类接口不可用，技能依然完整可用。

## 业务价值

1. **对用户的价值**：把"想吃麦当劳"与"热量/营养目标"两个决策合一，免去手动查营养成分表+心算组合的成本；家长、健身人群、控糖人群是高频受益群体。
2. **对麦当劳 MCP 的价值**：`list-nutrition-foods` 是纯数据型 Tool，本项目展示了它与本地算法结合的典型范式——MCP 提供权威数据、Skill 提供决策智能，可复制到"低钠点餐""儿童营养""运动补给"等更多垂直场景。
3. **对开发者的价值**：仓库同时提供 WorkBuddy 技能（对话式产品形态）与 Python 客户端（工程化调用示例），两种接入方式均开箱可跑。

## 真实调用证据

- 客户端实现见 [src/mcd_mcp_client.py](src/mcd_mcp_client.py)（完整 streamable HTTP 握手：initialize → notifications/initialized → tools/call）
- 命令行实跑：`python -m src.cli --calories 600 --protein 30 --budget 40`
- WorkBuddy 对话上下文见仓库中的 workbuddy.md（参赛后补充导出）
