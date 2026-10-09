"""The VN2 benchmark: a seasonal moving average and an order-up-to policy.

VN2 was an inventory planning competition organized by Nicolas Vandeput (SupChains) in 2025.
Page, results and citation: https://supchains.com/vn2-inventory-competition/

Usage, from the folder of this script:
    python vn2_play.py vn2_benchmark.py
    python vn2_benchmark.py                  # the same

It scores 4,334.0 EUR (weeks 3 to 8). It is the benchmark of the competition, with the arithmetic
of the competition code. Before each round:
1. The weeks with a shortage are set aside: their sales are missing when the in-stock flag is False.
2. Seasonality: the mean sales of each calendar week (ISO week number) over all Store x Product,
   divided by the mean of these 52 numbers. Simple and multiplicative.
3. Forecast: the mean of the last 13 weeks of deseasonalized sales, times the seasonal factor of
   each future week.
4. Order up to 4 weeks of forecast: the forecast of the next 4 weeks, minus the end inventory and
   the two orders in transit. Never below 0, rounded to a whole number.
"""
import numpy as np
import pandas as pd

MOVING_AVERAGE = 13  # weeks
COVERAGE = 4         # weeks of forecast the policy orders up to


def policy(sales, in_stock, master, state):
    sales = sales.copy()
    sales.columns = pd.to_datetime(sales.columns)
    in_stock = in_stock.copy()
    in_stock.columns = pd.to_datetime(in_stock.columns)
    sales[~in_stock] = np.nan  # a week with a shortage: the sales do not show the demand

    # Seasonal factors: the mean sales of each week number, normalized to a mean of 1.
    season = sales.mean().rename("Demand").to_frame()
    season["Week Number"] = season.index.isocalendar().week
    season = season.groupby("Week Number").mean()
    season = season / season.mean()

    # Deseasonalize the sales, then take the mean of the last 13 weeks.
    sales_weeks = sales.columns.isocalendar().week
    sales_no_season = sales / (season.loc[sales_weeks.values]).values.reshape(-1)
    base_forecast = sales_no_season.iloc[:, -MOVING_AVERAGE:].mean(axis=1)

    # Seasonalize it for the next 8 weeks.
    f_periods = pd.date_range(start=sales.columns[-1], periods=10, inclusive="neither", freq="W-MON")
    forecast = pd.DataFrame(data=base_forecast.values.reshape(-1, 1).repeat(len(f_periods), axis=1),
                            columns=f_periods, index=sales.index)
    forecast = forecast * (season.loc[f_periods.isocalendar().week.values]).values.reshape(-1)

    # Order up to the forecast of the next 4 weeks.
    order_up_to = forecast.iloc[:, :COVERAGE].sum(axis=1)
    net_inventory = state[["In Transit W+1", "In Transit W+2", "End Inventory"]].sum(axis=1)
    return (order_up_to - net_inventory).clip(lower=0).round(0).astype(int)


if __name__ == "__main__":
    import vn2_play

    vn2_play.main([__file__])
