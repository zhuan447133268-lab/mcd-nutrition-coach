# 麦当劳 MCP 工具参考

本 skill 依赖一个已连接的「麦当劳 MCP」提供实时数据。下方为各工具的**职责、调用顺序与约定**。
具体参数名以实际 MCP 连接暴露的 schema 为准——调用前先用工具描述核对参数，
**绝不臆造参数或返回值**。MCP 未返回数据时，对用户明说"该门店实时数据暂未获取"，
不要编数据、不要估价格。

## 工具清单与职责

| 工具 | 职责 | 触发时机 |
|------|------|----------|
| `list-nutrition-foods` | 取在售餐品的能量/蛋白质/脂肪/碳水/钠（**不返回单价和品类**，2026-10-14 实测；价格需经 `query-meals` 补） | 第 2 步，每次搭配前必调 |
| `query-nearby-stores` | 按位置定位附近门店 | 省钱联动第 1 步（用户提价格/优惠时） |
| `query-meals` | 确认指定门店在售餐品与实时价格 | 省钱联动第 2 步 |
| `query-store-coupons` | 查指定门店可用券 | 省钱联动第 3 步（门店维度） |
| `available-coupons` | 查账户/通用可用券 | 省钱联动第 3 步（账户维度，与上一者二选一或并用） |
| `calculate-price` | 按券复算组合实付金额 | 省钱联动第 4 步 |
| `create-order` | 创建订单 | 仅用户明确"下单/就这套"时 |

## 调用顺序

### 标准搭配流程（无优惠诉求）
```
list-nutrition-foods  →  （喂给 scripts/combo_search.py）→  呈现 3 套候选
```

### 省钱联动流程（用户提到价格 / 优惠 / 划算 / 券 时）
严格按顺序，缺一步就停下说明，不要跳步：
```
1. query-nearby-stores   定位门店（拿到 store_id）
2. query-meals           用 store_id 确认在售与实时价格
3. query-store-coupons | available-coupons   查券（优先门店券，再补账户券）
4. calculate-price       把券后价复算出来
```
把 `calculate-price` 得到的**券后实付**标注在推荐组合旁。

### 下单流程（仅用户明确说"下单 / 就这套"）
```
create-order  之前必须复述：门店 + 餐品明细 + 金额
→ 等用户确认
→ 执行 create-order
→ 返回 订单号 + 支付链接
```

## 数据约定（list-nutrition-foods 期望字段）
喂给 `scripts/combo_search.py` 的每条餐品至少包含：
`name, kcal, protein, fat, carb, sodium, price`，可选 `category`。
字段缺失时：缺失营养值按 0 处理并在呈现时标注"数据缺失"，缺失 `price` 则组合不参与省钱联动。

## 红线（与 SKILL.md 一致，重复强调）
- 不编造任何餐品的营养数据或价格。MCP 查不到就明说。
- 每套组合总热量不得超过用户设定上限，宁可少推不可超推。
- 输出末尾固定加：以上搭配仅供参考，不构成医疗或营养专业建议。
