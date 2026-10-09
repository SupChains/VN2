"""Simulate VN2 orders with the official rules of the competition.

VN2 was an inventory planning competition organized by Nicolas Vandeput (SupChains) in 2025.
Page, results and citation: https://supchains.com/vn2-inventory-competition/

Usage, from the folder of this script:
    python vn2_simulate.py "My orders"

"My orders" is a folder that holds six order files, named as in the competition:
"Week 1 - 2024-04-15 - Order.csv" to "Week 6 - 2024-05-20 - Order.csv". An order file has the
layout of "Data/Week 0 - Submission Template.csv": the columns Store and Product, then one column
of orders. 599 rows in the order of the template, whole numbers, 0 or more.

The rules, with the arithmetic of the competition code:
- Order k (k = 1 to 6) is placed before week k. It is on the shelf at the start of week k+2.
  Orders 7 and 8 are zero: they would arrive after week 8.
- The demand of a week is its sales in the data. Sales = min(start inventory, demand). Demand the
  shelf cannot serve is lost: there are no backorders.
- Holding cost: 0.2 EUR per unit left on the shelf at the end of a week. Goods in transit cost nothing.
- Shortage cost: 1 EUR per unit of lost sales.
- Weeks 1 and 2 are the setup: no order can change them. The score is the cost of weeks 3 to 8.

It also works as a library:
    from vn2_simulate import load, simulate
    weekly, score = simulate(orders, load())   # orders: six Series indexed by Store and Product
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

INDEX = ["Store", "Product"]
HERE = Path(__file__).resolve().parent
DATA = HERE / "Data"
WEEK_0 = pd.Timestamp("2024-04-08")  # the last week of history; week 1 starts on 2024-04-15
HOLDING_COST = 0.2   # EUR per unit left on the shelf at the end of a week
SHORTAGE_COST = 1.0  # EUR per unit of lost sales
ROUNDS = 6           # orders 1 to 6
WEEKS = 8            # weeks 1 to 8
SETUP = (1, 2)       # no order can change these weeks
SCORED = (3, 4, 5, 6, 7, 8)


class OrderError(ValueError):
    """An order that breaks the format rules of the competition."""


def week_date(week):
    """The Monday that labels a week: week 0 is 2024-04-08, week 1 is 2024-04-15."""
    return (WEEK_0 + pd.Timedelta(weeks=week)).strftime("%Y-%m-%d")


def read_table(path):
    """Read a VN2 file: one row per Store x Product."""
    path = Path(path)
    if not path.exists():
        sys.exit(f"File not found: {path}")
    return pd.read_csv(path).set_index(INDEX)


def sales_file(week, data=DATA):
    """The sales file the competitors received after week `week` (0 to 8)."""
    return Path(data) / f"Week {week} - {week_date(week)} - Sales.csv"


def load(data=DATA):
    """The files of the simulation. The Week 8 sales file holds every week, the demand of weeks 1 to 8 included."""
    data = Path(data)
    return {
        "folder": data,
        "sales": read_table(sales_file(WEEKS, data)),
        "in_stock": read_table(data / "Week 0 - In Stock.csv"),
        "master": read_table(data / "Week 0 - Master.csv"),
        "initial": read_table(data / f"Week 0 - {week_date(0)} - Initial State.csv"),
        "template": read_table(data / "Week 0 - Submission Template.csv"),
    }


def check_order(order, index, name="The order"):
    """The checks of the competition platform. Accepts a table read from an order file, a Series or
    a one-column table indexed by Store and Product, or 599 numbers in the order of the template.
    Returns the orders as a Series of whole numbers, indexed like the template."""
    if isinstance(order, pd.DataFrame) and not set(INDEX) <= set(order.index.names):
        if not set(INDEX) <= set(order.columns):
            raise OrderError(f"{name} needs the columns Store and Product.")
        order = order.set_index(INDEX)
    if isinstance(order, pd.Series):
        order = order.to_frame()
    if not isinstance(order, pd.DataFrame):  # numbers in the order of the template
        values = np.asarray(order)
        if values.ndim != 1:
            raise OrderError(f"{name} must be one number per Store x Product.")
        if len(values) != len(index):
            raise OrderError(f"{name} has {len(values)} rows. It needs {len(index)} rows.")
        order = pd.DataFrame({"Orders": values}, index=index)
    if order.shape[0] != len(index):
        raise OrderError(f"{name} has {order.shape[0]} rows. It needs {len(index)} rows, one per Store x Product.")
    if order.shape[1] != 1:
        raise OrderError(f"{name} has {order.shape[1]} columns besides Store and Product. It needs one column of orders.")
    if not order.index.equals(index):
        raise OrderError(f"{name}: the rows (Store x Product) are not those of the template, in the same order.")
    orders = pd.to_numeric(order.iloc[:, 0], errors="coerce").astype(float)
    empty = int((~np.isfinite(orders)).sum())
    if empty:
        raise OrderError(f"{name} has {empty} empty or non-numeric {'cell' if empty == 1 else 'cells'}.")
    if not (orders.round(0) == orders).all():
        raise OrderError(f"{name} has decimals. Orders must be whole numbers.")
    if not (orders >= 0).all():
        raise OrderError(f"{name} has negative orders.")
    return orders.astype(int).rename("Orders").set_axis(index)


def play_week(previous, demand, orders):
    """One week of the competition: the state at the end of the week, from the state at the end of
    the week before, the demand of the week and the order placed before the week."""
    state = pd.DataFrame(index=previous.index)
    state["Start Inventory"] = previous["End Inventory"] + previous["In Transit W+1"]
    state["Sales"] = state["Start Inventory"].clip(upper=demand)
    state["Missed Sales"] = demand - state["Sales"]
    state["End Inventory"] = state["Start Inventory"] - state["Sales"]
    state["In Transit W+1"] = previous["In Transit W+2"]
    state["In Transit W+2"] = orders
    state["Holding Cost"] = state["End Inventory"] * HOLDING_COST
    state["Shortage Cost"] = state["Missed Sales"] * SHORTAGE_COST
    state["Cumulative Holding Cost"] = previous["Cumulative Holding Cost"] + state["Holding Cost"]
    state["Cumulative Shortage Cost"] = previous["Cumulative Shortage Cost"] + state["Shortage Cost"]
    return state


def run(orders, data=None):
    """Play weeks 1 to 8 with six orders. Returns nine state tables, week 0 (the initial state) to
    week 8, one row per Store x Product, with the columns of the competition's state files."""
    data = load() if data is None else data
    sales = data["sales"]
    if len(orders) != ROUNDS:
        raise OrderError(f"The simulation needs six orders, one per round. It got {len(orders)}.")
    states = [data["initial"]]
    for week in range(1, WEEKS + 1):
        if week <= ROUNDS:
            order = check_order(orders[week - 1], sales.index, f"Order {week}")
        else:
            order = pd.Series(0, index=sales.index, name="Orders")
        states.append(play_week(states[-1], sales[week_date(week)], order))
    return states


def summarize(states):
    """One row per week, 1 to 8: the totals of the 599 Store x Product and the cost of the week."""
    rows = []
    for week, state in enumerate(states[1:], start=1):
        total = state.sum()
        rows.append({
            "Week": week,
            "Date": week_date(week),
            "Start Inventory": total["Start Inventory"],
            "Sales": total["Sales"],
            "Lost Sales": total["Missed Sales"],
            "End Inventory": total["End Inventory"],
            "In Transit": total["In Transit W+1"] + total["In Transit W+2"],
            "Holding Cost": total["Holding Cost"],
            "Shortage Cost": total["Shortage Cost"],
        })
    weekly = pd.DataFrame(rows).set_index("Week")
    weekly["Cost"] = weekly["Holding Cost"] + weekly["Shortage Cost"]
    return weekly


def setup(weekly):
    """The cost of weeks 1 and 2, the same for every player."""
    return round(float(weekly.loc[list(SETUP), "Cost"].sum()), 1)


def score(weekly):
    """The score of the competition: the cost of weeks 3 to 8."""
    return round(float(weekly.loc[list(SCORED), "Cost"].sum()), 1)


def simulate(orders, data=None):
    """Play six orders with the official rules. Returns (weekly, score): the table of summarize()
    and the cost of weeks 3 to 8."""
    weekly = summarize(run(orders, data))
    return weekly, score(weekly)


def print_costs(weekly):
    """The cost per week, the setup and the score, as text."""
    print("Week  Date         Holding  Shortage      Cost")
    for week, row in weekly.iterrows():
        note = "   setup" if week in SETUP else ""
        print(f"{week:4d}  {row['Date']}  {row['Holding Cost']:7.1f}  {row['Shortage Cost']:8.1f}  {row['Cost']:8.1f}{note}")
    print()
    print(f"Setup, weeks 1 and 2 (the same for every player): {setup(weekly):9,.1f} EUR")
    print(f"Score, the cost of weeks 3 to 8:                   {score(weekly):9,.1f} EUR")


def read_orders(folder):
    """The six order files of a folder: "Week k - <date> - Order.csv", k = 1 to 6."""
    folder = Path(folder)
    if not folder.is_dir():
        sys.exit(f"Folder not found: {folder}")
    orders = []
    for week in range(1, ROUNDS + 1):
        name = f"Week {week} - {week_date(week)} - Order.csv"
        found = [p for p in folder.iterdir() if p.name.lower() == name.lower()]
        if not found:
            sys.exit(f'{folder.name}: the file "{name}" is missing.')
        orders.append(pd.read_csv(found[0]))
    return orders


def main():
    parser = argparse.ArgumentParser(description="Simulate six VN2 orders with the official rules and print the score.")
    parser.add_argument("orders", help='a folder that holds "Week 1 - 2024-04-15 - Order.csv" to "Week 6 - 2024-05-20 - Order.csv"')
    parser.add_argument("--data", default=str(DATA),
                        help="the folder that holds the competition files (default: Data, next to this script)")
    args = parser.parse_args()

    orders = read_orders(args.orders)
    try:
        weekly, _ = simulate(orders, load(args.data))
    except OrderError as error:
        sys.exit(str(error))
    print_costs(weekly)


if __name__ == "__main__":
    main()
