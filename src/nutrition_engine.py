"""营养搭配引擎：约束过滤 + 组合搜索 + 评分排序。

不内置任何餐品数据——所有条目均来自 list-nutrition-foods 的实时返回。
官方接口字段名若发生变化，只需调整 FIELD_MAP。
"""
from dataclasses import dataclass, field
from itertools import combinations

# list-nutrition-foods 返回字段 → 引擎内部字段（以官方工具实际返回为准）
FIELD_MAP = {
    "name": "name",
    "energy": "kcal",        # 能量(kcal)
    "protein": "protein",    # 蛋白质(g)
    "fat": "fat",            # 脂肪(g)
    "carbohydrate": "carbs", # 碳水化合物(g)
    "sodium": "sodium",      # 钠(mg)
    "price": "price",        # 价格(元)，营养接口未返回时由 query-meals 补充
}


@dataclass
class Item:
    name: str
    kcal: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    sodium: float = 0.0
    price: float = 0.0


@dataclass
class Goal:
    max_kcal: float = 600.0
    protein_target: float = 0.0
    max_price: float = 0.0       # 0 表示不限
    max_sodium: float = 0.0      # 0 表示不限
    max_items: int = 3
    top_n: int = 3


@dataclass
class Combo:
    items: list
    total: dict = field(default_factory=dict)
    score: float = 0.0


def normalize(raw: dict) -> Item | None:
    """把一条原始数据归一化为 Item；没有可识别营养字段的条目直接丢弃。"""
    try:
        vals = {v: float(raw.get(k) or 0) for k, v in FIELD_MAP.items() if k != "name"}
    except (TypeError, ValueError):
        return None
    if vals["kcal"] <= 0:
        return None
    return Item(name=str(raw.get(FIELD_MAP["name"], "未命名")), **vals)


def _score(c: Combo, goal: Goal) -> float:
    """蛋白质达成度越高越好，同时惩罚脂肪占比过高，略微鼓励荤素多样。"""
    p = c.total["protein"]
    kcal = max(c.total["kcal"], 1.0)
    protein_score = min(p / goal.protein_target, 1.5) if goal.protein_target else 0.0
    fat_penalty = c.total["fat"] * 9 / kcal  # 脂肪供能占比
    variety = len(c.items) * 0.05
    return protein_score - fat_penalty + variety


def suggest(items: list[Item], goal: Goal) -> list[Combo]:
    """搜索满足硬约束的组合，按评分返回前 top_n 套。"""
    pool = [it for it in items if it.kcal <= goal.max_kcal]
    best: list[Combo] = []
    for n in range(1, goal.max_items + 1):
        for pick in combinations(pool, n):
            total = {
                "kcal": sum(i.kcal for i in pick),
                "protein": sum(i.protein for i in pick),
                "fat": sum(i.fat for i in pick),
                "carbs": sum(i.carbs for i in pick),
                "sodium": sum(i.sodium for i in pick),
                "price": sum(i.price for i in pick),
            }
            if total["kcal"] > goal.max_kcal:
                continue
            if goal.max_price and total["price"] > goal.max_price:
                continue
            if goal.max_sodium and total["sodium"] > goal.max_sodium:
                continue
            combo = Combo(items=list(pick), total=total)
            combo.score = round(_score(combo, goal), 3)
            best.append(combo)
    best.sort(key=lambda c: c.score, reverse=True)
    return best[: goal.top_n]
