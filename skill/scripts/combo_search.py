#!/usr/bin/env python3
"""麦当劳营养组合搜索（确定性、可复算）。

从麦当劳 MCP 在运行时取回的餐品数据 + 用户约束出发，暴力枚举最多
`max_items` 件不同餐品的所有组合，按硬约束过滤，再对可行组合打分排序，
输出 Top-N 候选（JSON）。

餐品数据字段（每项）：
  name      str   餐品名称（必须与 MCP 返回完全一致，禁止改写）
  kcal      number 能量（千卡）
  protein   number 蛋白质（克）
  fat       number 脂肪（克）
  carb      number 碳水（克）
  sodium    number 钠（毫克）
  price     number 单价（货币单位）
  category  str|None  可选，用于"品类多样"软指标；缺省不参与惩罚

约束（CLI 参数，除 max_items/top 外均为可选）：
  --kcal-cap       float  硬约束：组合总热量 <= 上限
  --protein-target float  软目标：优先让蛋白质达成度最高
  --budget         float  硬约束：组合总价 <= 预算
  --sodium-cap     float  硬约束：组合总钠 <= 上限
  --max-items      int=3  组合中不同餐品最多件数
  --top            int=3  返回的候选套数

输出：JSON 数组，每项为一套候选：
  {
    "items": [ {name,kcal,protein,fat,carb,sodium,price,category}, ... ],
    "totals": {kcal,protein,fat,carb,sodium,price,fat_energy_pct,categories},
    "score": float,
    "feasible": true
  }

排序规则（严格按用户指定优先级）：
  1) 蛋白质达成度最高（达成度 = min(总蛋白/目标, 1.0)；设了目标才用，否则按总蛋白高优先）
  2) 脂肪供能占比低（fat*9 / kcal * 100，越低越好）
  3) 品类多样（distinct category 数，越多越好）
  4) 已达成的组合中，总热量更低者优先（减少浪费）
红线：任何组合总热量超过 --kcal-cap 一律剔除（宁可少推不可超推）。
"""
import argparse
import json
import sys
from itertools import combinations


def parse_foods(raw):
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw
    if not isinstance(data, list):
        raise ValueError("餐品数据必须是 JSON 数组")
    foods = []
    for i, f in enumerate(data):
        item = {
            "name": str(f.get("name", f"item_{i}")),
            "kcal": float(f.get("kcal", 0) or 0),
            "protein": float(f.get("protein", 0) or 0),
            "fat": float(f.get("fat", 0) or 0),
            "carb": float(f.get("carb", 0) or 0),
            "sodium": float(f.get("sodium", 0) or 0),
            "price": float(f.get("price", 0) or 0),
            "category": f.get("category"),
        }
        foods.append(item)
    return foods


def fat_energy_pct(combo):
    kcal = sum(c["kcal"] for c in combo)
    if kcal <= 0:
        return 0.0
    return (sum(c["fat"] for c in combo) * 9.0) / kcal * 100.0


def totals(combo):
    cats = {c["category"] for c in combo if c.get("category")}
    return {
        "kcal": round(sum(c["kcal"] for c in combo), 1),
        "protein": round(sum(c["protein"] for c in combo), 1),
        "fat": round(sum(c["fat"] for c in combo), 1),
        "carb": round(sum(c["carb"] for c in combo), 1),
        "sodium": round(sum(c["sodium"] for c in combo), 1),
        "price": round(sum(c["price"] for c in combo), 2),
        "fat_energy_pct": round(fat_energy_pct(combo), 1),
        "categories": sorted(cats) if cats else [],
    }


def feasible(combo, kcal_cap, budget, sodium_cap):
    t = totals(combo)
    if kcal_cap is not None and t["kcal"] > kcal_cap:
        return False
    if budget is not None and t["price"] > budget:
        return False
    if sodium_cap is not None and t["sodium"] > sodium_cap:
        return False
    return True


def rank_key(combo, protein_target):
    """返回排序元组，值越小排名越前（严格按用户指定优先级）：
    1) 蛋白质达成度最高（达成度 = min(总蛋白/目标, 1.0)；无目标则按总蛋白高）
    2) 脂肪供能占比低
    3) 品类多样（distinct category 数多）
    4) 总热量更低（已达成的组合减少浪费）
    """
    t = totals(combo)
    if protein_target:
        achievement = min(t["protein"] / protein_target, 1.0)
        primary = -achievement
    else:
        primary = -t["protein"]
    diversity = len(t["categories"])
    return (primary, fat_energy_pct(combo), -diversity, t["kcal"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="餐品 JSON 文件路径；缺省读 stdin")
    ap.add_argument("--kcal-cap", type=float, default=None)
    ap.add_argument("--protein-target", type=float, default=None)
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--sodium-cap", type=float, default=None)
    ap.add_argument("--max-items", type=int, default=3)
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args()

    raw = None
    if args.input:
        with open(args.input, "r", encoding="utf-8") as fh:
            raw = fh.read()
    else:
        raw = sys.stdin.read()
    foods = parse_foods(raw)

    candidates = []
    n = len(foods)
    for size in range(1, args.max_items + 1):
        for idx in combinations(range(n), size):
            combo = [foods[i] for i in idx]
            if feasible(combo, args.kcal_cap, args.budget, args.sodium_cap):
                candidates.append(combo)

    if not candidates:
        out = {
            "feasible_count": 0,
            "candidates": [],
            "note": "在给定约束内无任何可行组合，请放宽热量/预算/钠上限或增加餐品候选。",
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    candidates.sort(key=lambda c: rank_key(c, args.protein_target))
    top = candidates[: max(1, args.top)]

    result = []
    for combo in top:
        result.append(
            {
                "items": combo,
                "totals": totals(combo),
                "score": round(rank_key(combo, args.protein_target)[0], 4),
                "feasible": True,
            }
        )

    out = {
        "feasible_count": len(candidates),
        "returned": len(result),
        "constraints": {
            "kcal_cap": args.kcal_cap,
            "protein_target": args.protein_target,
            "budget": args.budget,
            "sodium_cap": args.sodium_cap,
            "max_items": args.max_items,
        },
        "candidates": result,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
