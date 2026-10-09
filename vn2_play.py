"""Replay the VN2 inventory competition with your own ordering policy.

VN2 was an inventory planning competition organized by Nicolas Vandeput (SupChains) in 2025.
Page, results and citation: https://supchains.com/vn2-inventory-competition/

Usage, from the folder of this script:
    python vn2_play.py my_policy.py
    python vn2_play.py vn2_benchmark.py      # the benchmark of the competition

my_policy.py defines one function:

    def policy(sales, in_stock, master, state):
        ...
        return orders

The four arguments are pandas DataFrames indexed by Store and Product, read from the competition
files. Before round k (k = 1 to 6), they hold what the competitors had at that time, and nothing more:
- sales: the weekly sales up to week k-1, the file "Week k-1 - <date> - Sales.csv". Week 0 is
  2024-04-08. One column per week, labelled with its Monday date as text ("2024-04-08").
- in_stock: the in-stock flags of the same weeks. "Week 0 - In Stock.csv" also holds the later
  weeks: they are cut.
- master: the file "Week 0 - Master.csv", the product and store hierarchy.
- state: your inventory state at the end of week k-1 (the initial state before round 1), with the
  columns of the competition's state files: End Inventory, In Transit W+1, In Transit W+2...

orders: 599 whole numbers, 0 or more. A Series indexed by Store and Product like the template, or
a list in the order of the template. Order k is on the shelf at the start of week k+2.

The script plays weeks 1 to 8 with the rules of vn2_simulate.py (orders 7 and 8 are zero, as in
the competition), writes the six order files in a folder "Orders - my_policy", and prints the cost
per week, the setup, the score and where the score would rank in the final ranking.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

from vn2_simulate import (DATA, ROUNDS, WEEKS, OrderError, check_order, load, play_week, print_costs,
                          read_table, sales_file, score, summarize, week_date)

# The final ranking: the cost of weeks 3 to 8, in EUR.
RANKING = [
    ("1st: Bartosz Szabłowski", 3763.2),
    ("2nd: Matias Alvo", 3764.6),
    ("3rd: Philip Stubbs and Jakub Figura", 3791.6),
    ("4th: Carlo Cavalieri", 3794.4),
    ("5th: Ruben van de Geer, Diederik Perdok and Simon Grest", 3824.4),
    ("Benchmark (vn2_benchmark.py)", 4334.0),
]
TOP_5 = [result for name, result in RANKING if not name.startswith("Benchmark")]
BENCHMARK = RANKING[-1][1]


def load_policy(path):
    """Import the function policy() of a Python file."""
    path = Path(path).resolve()
    if not path.exists():
        sys.exit(f"File not found: {path}")
    sys.path.insert(0, str(path.parent))  # the policy may import its own helpers
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "policy", None)):
        sys.exit(f"{path.name} must define a function policy(sales, in_stock, master, state).")
    return module.policy


def play(policy, data=None):
    """Play the six rounds with a policy. Returns the six orders and the nine states (week 0 to 8)."""
    data = load() if data is None else data
    index = data["sales"].index
    states, orders = [data["initial"]], []
    for week in range(1, WEEKS + 1):
        if week <= ROUNDS:
            sales = read_table(sales_file(week - 1, data["folder"]))
            in_stock = data["in_stock"][sales.columns]  # no flag after week k-1
            order = policy(sales.copy(), in_stock.copy(), data["master"].copy(), states[-1].copy())
            order = check_order(order, index, f"Order {week} (before week {week}, {week_date(week)})")
            orders.append(order)
        else:
            order = pd.Series(0, index=index, name="Orders")
        states.append(play_week(states[-1], data["sales"][week_date(week)], order))
    return orders, states


def ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def print_ranking(value):
    """The score beside the final ranking."""
    rows = RANKING + [("Your policy", value)]
    for name, result in sorted(rows, key=lambda row: row[1]):
        mark = "   <- your policy" if name == "Your policy" else ""
        print(f"  {result:9,.1f}  {'' if mark else name}{mark}")
    print()
    rank = 1 + sum(result < value for result in TOP_5)
    if rank <= len(TOP_5):
        print(f"Your score would rank {ordinal(rank)} in the final ranking.")
    else:
        print("Your score would rank behind the top 5.")
    gap = round(BENCHMARK - value, 1)
    if gap == 0:
        print("It equals the benchmark.")
    else:
        side = "below" if gap > 0 else "above"
        print(f"It is {abs(gap):,.1f} EUR ({abs(gap) / BENCHMARK:.1%}) {side} the benchmark.")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # a console that cannot show a letter prints "?"
    parser = argparse.ArgumentParser(description="Replay the six rounds of VN2 with your policy and print the score.")
    parser.add_argument("policy", help="a Python file that defines policy(sales, in_stock, master, state)")
    parser.add_argument("--out", help='the folder for the six order files (default: "Orders - <policy file name>")')
    parser.add_argument("--data", default=str(DATA),
                        help="the folder that holds the competition files (default: Data, next to this script)")
    args = parser.parse_args(argv)

    policy = load_policy(args.policy)
    try:
        orders, states = play(policy, load(args.data))
    except OrderError as error:
        sys.exit(str(error))

    out = Path(args.out) if args.out else Path.cwd() / f"Orders - {Path(args.policy).stem}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"Policy: {Path(args.policy).name}")
    for week, order in enumerate(orders, start=1):
        name = f"Week {week} - {week_date(week)} - Order.csv"
        order.to_frame().to_csv(out / name)
        print(f"  Order {week}, before week {week}: {int(order.sum()):6,d} units  -> {out.name}/{name}")
    print()

    weekly = summarize(states)
    print_costs(weekly)
    print()
    print_ranking(score(weekly))


if __name__ == "__main__":
    main()
