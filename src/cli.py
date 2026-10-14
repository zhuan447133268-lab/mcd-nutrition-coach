"""命令行入口：python -m src.cli --calories 600 --protein 30 --budget 40"""
import argparse
import asyncio
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.mcd_mcp_client import list_nutrition_foods
from src.nutrition_engine import Goal, normalize, suggest


async def main() -> None:
    ap = argparse.ArgumentParser(description="麦麦营养教练：按目标搭配麦当劳餐品")
    ap.add_argument("--calories", type=float, default=600, help="热量上限(kcal)")
    ap.add_argument("--protein", type=float, default=0, help="蛋白质目标(g)")
    ap.add_argument("--budget", type=float, default=0, help="预算上限(元)，0 不限")
    ap.add_argument("--sodium", type=float, default=0, help="钠上限(mg)，0 不限")
    ap.add_argument("--max-items", type=int, default=3, help="组合内最多餐品数")
    args = ap.parse_args()

    raw = await list_nutrition_foods()
    items = [it for it in (normalize(r) for r in raw) if it]
    if not items:
        raise SystemExit("未获取到有效营养数据，请检查 MCP Token 或接口返回结构。")

    goal = Goal(max_kcal=args.calories, protein_target=args.protein,
                max_price=args.budget, max_sodium=args.sodium,
                max_items=args.max_items)
    combos = suggest(items, goal)
    if not combos:
        print("当前约束下没有可行组合，试试放宽热量或预算。")
        return

    for rank, c in enumerate(combos, 1):
        print(f"\n=== 方案 {rank}（评分 {c.score}）===")
        for i in c.items:
            print(f"  · {i.name}  {i.kcal:.0f}kcal  蛋白质{i.protein:.1f}g"
                  + (f"  ¥{i.price:.1f}" if i.price else ""))
        t = c.total
        print(f"  合计: {t['kcal']:.0f}kcal | 蛋白质 {t['protein']:.1f}g | "
              f"脂肪 {t['fat']:.1f}g | 碳水 {t['carbs']:.1f}g | 钠 {t['sodium']:.0f}mg"
              + (f" | ¥{t['price']:.1f}" if t["price"] else ""))


if __name__ == "__main__":
    asyncio.run(main())
