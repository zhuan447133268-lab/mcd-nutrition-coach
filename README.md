# mcd-nutrition-coach · 麦麦营养教练

基于**麦当劳 MCP** 的智能点餐搭配助手：输入你的热量/蛋白质/预算目标，自动从麦当劳在售餐品中搭配出合适的套餐组合，让"吃麦当劳"和"健康目标"不再打架。

> 本项目为「1024程序员节 · 麦当劳程序员创意开发大赛」参赛作品，由参赛者独立开发，非麦当劳官方产品。项目输出仅供参考，不构成医疗、营养或其他专业建议；餐品信息、价格及供应状态以麦当劳官方渠道的实时结果为准。

## 它能做什么

- 🎯 **按目标搭配**：设定每餐热量上限（如 600 kcal）、蛋白质目标（如 30 g）、预算（如 40 元），给出 3 套候选组合并标注取舍
- 🥗 **场景模板**：健身增肌 / 控脂减重 / 给孩子点餐（低钠低糖）/ 均衡日常，一键带入预设约束
- 🧮 **营养计算**：调用麦当劳官方 MCP 的 `list-nutrition-foods` 获取真实营养数据，组合计算总热量、蛋白质、脂肪、碳水、钠
- 💰 **省钱联动（可选）**：搭配结果可继续调用 `query-store-coupons` / `calculate-price`，用可用优惠券复算价格
- 🤖 **两种用法**：WorkBuddy 技能（对话式，推荐）+ Python CLI（开发者脚本）

## 目标用户

| 用户 | 场景 |
|---|---|
| 健身/减脂人群 | 增肌期要高蛋白、减脂期要控热量，麦当劳也能吃得有数 |
| 家长 | 给孩子搭配低钠、低糖、营养均衡的儿童餐组合 |
| 控糖/慢病管理人群 | 按碳水、钠含量约束选餐 |
| 普通上班族 | 快速知道"这一顿吃了多少"，避免无意识超标 |

## 安装与使用

### 方式一：WorkBuddy 技能（推荐）

前置条件：已申请麦当劳 MCP Token，并在 WorkBuddy 中配置启用 `mcd-mcp` 连接器（见 [mcp-config.example.json](mcp-config.example.json)）。

1. 将 [skill/SKILL.md](skill/SKILL.md) 按 WorkBuddy 技能的格式导入（或直接把技能内容粘贴为自定义技能）
2. 在对话框中说出目标，例如：
   - 「我在减脂，午餐预算 35，帮我搭配一套不超过 550 大卡的麦当劳」
   - 「增肌期，目标蛋白质 40g，给我三套组合对比一下」
   - 「给孩子点个营养晚餐，钠含量要低」
3. 技能会引导 AI 调用麦当劳 MCP 工具完成搭配

### 方式二：Python CLI

```bash
pip install -r requirements.txt
set MCD_MCP_TOKEN=你的Token        # Windows
python -m src.cli --calories 600 --protein 30 --budget 40
```

CLI 通过 streamable HTTP 直连 `https://mcp.mcd.cn` 调用 `list-nutrition-foods` 获取真实营养数据，再由本地营养引擎组合择优。

## 项目结构

```
├── README.md                  # 本文件
├── CONTEST_DECLARATION.md     # 参赛声明（官方模板，不可修改）
├── MCP_INTEGRATION.md         # MCP 工具调用说明
├── mcp-config.example.json    # 脱敏 MCP 配置示例（仅环境变量占位符）
├── requirements.txt
├── skill/                     # WorkBuddy 技能（在 WorkBuddy 中实际开发生成，已实测）
│   ├── SKILL.md               # 技能定义：四步工作流+省钱联动+下单确认+红线
│   ├── scripts/combo_search.py # 确定性组合搜索（stdin 喂餐品JSON，输出Top-N候选）
│   └── references/mcp_tools.md # MCP工具职责/调用顺序/数据约定
└── src/
    ├── mcd_mcp_client.py      # 麦当劳 MCP streamable HTTP 客户端
    ├── nutrition_engine.py    # 组合搭配与营养计算引擎
    └── cli.py                 # 命令行入口
```

## 技术要点

- **数据驱动**：营养引擎不内置任何餐品数据，全部来自 `list-nutrition-foods` 实时返回，字段映射集中在 `nutrition_engine.FIELD_MAP` 一处，官方接口字段变化时只需改这里
- **组合择优**：在满足硬约束（热量上限、预算）的组合中，按蛋白质达成度与营养均衡度评分排序
- **可解释**：每套组合都列出明细、小计和"超/达标"标注，不玩黑箱

## 免责说明

营养数据以麦当劳 MCP 返回为准；不同门店供应与配方可能不同。特殊健康状况请咨询医生或注册营养师。
