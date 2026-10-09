# VN2 Inventory Planning Challenge: data, simulator and benchmark

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23265105-blue.svg)](https://doi.org/10.5281/zenodo.23265105)

VN2 was an inventory planning competition organized by Nicolas Vandeput ([SupChains](https://supchains.com/))
in 2025, the first public inventory planning competition. Over 180 participants ordered stock for
599 products in the stores of a retail chain, over six weekly rounds. The lowest cost won.

This repository holds the data, the official simulator, the benchmark and a script that replays the
six rounds with your own ordering policy. [Flieber](https://www.flieber.com/), [Daybreak](https://daybreak.ai/)
and SupChains sponsored the competition, and [DataSource.ai](https://www.datasource.ai/en/home/data-science-competitions-for-startups/vn2-inventory-planning-challenge/description)
hosted it.

- **Page, with the results:** https://supchains.com/vn2-inventory-competition/
- **Webinar, the winners explain their solutions (December 2025):** https://www.youtube.com/watch?v=pypzcvwmApA
- **Article, my learning points from VN2:** https://nicolas-vandeput.medium.com/my-learning-points-from-vn2-the-first-inventory-competition-a4bffcc92856
- **How to cite VN2:** [at the end of this page](#how-to-cite-vn2), and in [CITATION.cff](CITATION.cff)

## Start here

The scripts need Python 3 with pandas and NumPy. Run them from the root of this repository.

```
pip install -r requirements.txt
python vn2_play.py vn2_benchmark.py
```

The benchmark must print a setup of 913.8 € and a score of 4,334.0 €. Then write your own policy
(see [How to play](#how-to-play)) and replay the competition with it.

The scripts were tested with Python 3.13, pandas 3.0 and NumPy 2.4.

## The scenario

It is Monday 15 April 2024, early in the morning. You are the inventory planner of a retail chain.
Every week, before the stores open, you order stock from the central warehouse. It arrives two
weeks later. You know your stock, the orders on their way, and about three years of weekly sales.

You place six orders, one per week. Each order should keep the shelves stocked without leaving
too much on them.

## The rules

- **Holding cost**: 0.2 € per unit left on the shelf at the end of a week. Goods in transit cost
  nothing. Stock does not expire.
- **Shortage cost**: 1 € per unit of lost sales. There are no backorders: a sale the shelf cannot
  serve is lost.
- **Lead time**: you place order k before week k starts. It is on the shelf at the start of week
  k+2. Order 1 arrives in week 3, order 6 in week 8.
- **Supply**: the warehouse delivers every order in full, always in two weeks.
- **Setup**: weeks 1 and 2 are played with the stock and the orders you start with. No order can
  change them, so they cost 913.8 € to every player.
- **Score**: the cost of weeks 3 to 8. The lowest score wins.

Each round, a week of sales is played and you see it before your next order:

| Round | You know the sales up to | You order before | The order arrives in |
|---|---|---|---|
| 1 | Week 0, 8 April 2024 | Week 1, 15 April | Week 3, 29 April |
| 2 | Week 1, 15 April | Week 2, 22 April | Week 4, 6 May |
| 3 | Week 2, 22 April | Week 3, 29 April | Week 5, 13 May |
| 4 | Week 3, 29 April | Week 4, 6 May | Week 6, 20 May |
| 5 | Week 4, 6 May | Week 5, 13 May | Week 7, 27 May |
| 6 | Week 5, 13 May | Week 6, 20 May | Week 8, 3 June |

Weeks 7 and 8 are played with no new order: an order placed then would arrive after week 8.

The competition ran in 2025. The data came out on 29 September. The six rounds ran from
21 October to 5 November.

## What this repository holds

| File or folder | What it holds |
|---|---|
| `Data/Week 0 - 2024-04-08 - Sales.csv` | Units sold per week, 157 weeks, from 12 April 2021 to 8 April 2024: what you know before round 1 |
| `Data/Week 0 - In Stock.csv` | The in-stock flag of every week, up to 3 June 2024 |
| `Data/Week 0 - Master.csv` | The product and store hierarchy |
| `Data/Week 0 - 2024-04-08 - Initial State.csv` | The stock at the end of week 0 and the orders in transit, the same for every player |
| `Data/Week 0 - Submission Template.csv` | The layout of an order |
| `Data/Week 1 - 2024-04-15 - Sales.csv` to `Data/Week 8 - 2024-06-03 - Sales.csv` | The sales file of each round: each one adds a week |
| `vn2_simulate.py` | The official rules: it plays six orders and prints the score |
| `vn2_play.py` | Replays the six rounds with your ordering policy |
| `vn2_benchmark.py` | The benchmark of the competition, as a policy |
| `Benchmark/` | The six order files of the benchmark, as `vn2_play.py` writes them |
| `CITATION.cff` | The citation, for GitHub's "Cite this repository" and for reference managers |
| `LICENSE`, `LICENSE-DATA` | The licenses of the code and of the data |

## The data

The sales are real. They come from the stores of an anonymous retail chain. Each row is one
product in one store: 599 rows, 67 stores and 297 products. Two columns identify a row, `Store`
and `Product`. They are anonymized integer codes. Every file lists the same 599 rows in the same
order.

Every other column is one week, labelled with its Monday date (`2024-04-08`). Sales are whole
units. A week's sales are also its demand in the simulation.

The in-stock flag is `True` when some stock was left at the end of the week. It is `False` when
the shelf was empty at the end of the week: the sales of that week may be lower than the demand.
Most products ran out of stock in the past. As this is real data, some flags may be wrong.

The master file gives each row its `ProductGroup`, `Division`, `Department` and `DepartmentGroup`,
and the `StoreFormat` and `Format` of its store. They are anonymized codes too.

An order file has the layout of `Week 0 - Submission Template.csv`: the columns `Store` and
`Product`, then one column of orders. It holds 599 rows in the order of the template, whole
numbers, 0 or more.

## How to play

Write your policy in a Python file, `my_policy.py`, as one function:

```python
def policy(sales, in_stock, master, state):
    ...
    return orders  # 599 whole numbers, 0 or more, indexed by Store and Product
```

Then replay the competition with it:

    python vn2_play.py my_policy.py

Before each round, `vn2_play.py` gives your policy what the competitors had at that time, and
nothing more: the sales up to the week before, the in-stock flags of the same weeks, the master
file, and your stock and orders in transit at the end of the week before. It checks each order
like the competition did. It plays the eight weeks and prints the cost of each week, the setup,
your score and where it would rank. It writes your six orders in the folder `Orders - my_policy`.

To score six order files you made another way, name them like the competition did,
`Week 1 - 2024-04-15 - Order.csv` to `Week 6 - 2024-05-20 - Order.csv`, put them in one folder
and run:

    python vn2_simulate.py "Orders - my_policy"

`vn2_simulate.py` also works as a library:

```python
from vn2_simulate import load, simulate
weekly, score = simulate(orders, load())   # orders: six Series indexed by Store and Product
```

## The score

    Score = Σ over weeks 3 to 8 of (0.2 € × units left at the end of the week + 1 € × units of lost sales)

The competition played every order with this code, once per week:

```python
state["Start Inventory"] = previous_state["End Inventory"] + previous_state["In Transit W+1"]
state["Sales"] = state["Start Inventory"].clip(upper=demand)
state["Missed Sales"] = demand - state["Sales"]
state["End Inventory"] = state["Start Inventory"] - state["Sales"]
state["In Transit W+1"] = previous_state["In Transit W+2"]
state["In Transit W+2"] = orders
state["Holding Cost"] = state["End Inventory"] * 0.2
state["Shortage Cost"] = state["Missed Sales"] * 1.0
```

Judging an inventory policy is harder than judging a forecast. The only way is to see which
policy results in the lowest total cost over time.

## The benchmark

`vn2_benchmark.py` forecasts with a seasonal moving average and orders up to four weeks of
forecast. It takes 55 lines of Python.

1. It sets aside the weeks with a shortage, using the in-stock flag.
2. It computes one seasonal factor per calendar week, from the mean sales of all rows.
3. It forecasts with the mean of the last 13 weeks of deseasonalized sales, reseasonalized.
4. Each order brings the stock on the shelf and in transit up to the forecast of the next four
   weeks.

Over the eight weeks, it costs 5,247.8 €: 913.8 € of setup and a score of 4,334.0 €.

The benchmark was not optimized, and its four-week coverage was too long. With 3.5 weeks, it would
have scored about 3,900 €, the sixth place.

The folder `Benchmark/Orders - vn2_benchmark/` holds its six order files. Check them with
`python vn2_simulate.py "Benchmark/Orders - vn2_benchmark"`.

## Results

| Final ranking | Score |
|---|---|
| 1st: Bartosz Szabłowski | 3,763.2 € |
| 2nd: Matias Alvo | 3,764.6 € |
| 3rd: Philip Stubbs and Jakub Figura | 3,791.6 € |
| 4th: Carlo Cavalieri | 3,794.4 € |
| 5th: Ruben van de Geer, Diederik Perdok and Simon Grest | 3,824.4 € |
| 26th: Benchmark | 4,334.0 € |

Only 25 of the 180 participants beat the benchmark, and most end-to-end models did not. The winner
cost 13% less than the benchmark.

Weekly cost of the benchmark, in €:

| Week | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Holding | 158.6 | 204.2 | 637.8 | 573.4 | 478.2 | 487.2 | 487.0 | 592.4 |
| Shortage | 222.0 | 329.0 | 147.0 | 342.0 | 255.0 | 116.0 | 117.0 | 101.0 |
| Cost | 380.6 | 533.2 | 784.8 | 915.4 | 733.2 | 603.2 | 604.0 | 693.4 |

Weeks 1 and 2 are the setup, 913.8 € for every player.

## What the winners did

After the competition, I interviewed the top 20 about their methods.

- Each of them tested and tuned their policy on the past, by simulation.
- They projected their inventory to the week the order arrives, with the shortages expected before it.
- Mean forecasts and probabilistic forecasts both reached the top 5. LightGBM and CatBoost led the forecasts.
- The second place used reinforcement learning to place the orders.
- No participant using DDMRP, ABC segmentation or demand-pattern classes beat the benchmark.

At SupChains, we [set inventory targets the same way](https://supchains.com/inventory-planning-model/),
by simulation on real demand and real forecasts. The orders of the winners are not in this
repository.

## Learn more

- The winners explain their solutions, webinar of December 2025: https://www.youtube.com/watch?v=pypzcvwmApA
- My learning points from VN2, the first inventory competition, on Medium: https://nicolas-vandeput.medium.com/my-learning-points-from-vn2-the-first-inventory-competition-a4bffcc92856
- The Nixtla webinar on forecasting models for VN2: https://www.youtube.com/watch?v=0kGr8twWjag
- VN1, the forecasting competition of 2024: https://github.com/SupChains/VN1
- *Inventory Optimization: Models and Simulations*, the book: https://supchains.com/resources-invopt/
- The original competition pages on DataSource.ai: https://www.datasource.ai/en/home/data-science-competitions-for-startups/vn2-inventory-planning-challenge/description
- Flieber: https://www.flieber.com/ and Daybreak: https://daybreak.ai/

## How to cite VN2

The data is free to use. When you use it, please cite the competition:

> Vandeput, N. (2025). VN2 Inventory Planning Challenge. Organized by Nicolas Vandeput
> (SupChains). Sponsored by Flieber, Daybreak and SupChains.
> https://supchains.com/vn2-inventory-competition/

```bibtex
@misc{vandeput2025vn2,
  author       = {Vandeput, Nicolas},
  title        = {{VN2} Inventory Planning Challenge},
  year         = {2025},
  howpublished = {\url{https://supchains.com/vn2-inventory-competition/}},
  note         = {Organized by Nicolas Vandeput (SupChains). Sponsored by Flieber, Daybreak and SupChains.}
}
```

GitHub's "Cite this repository" button gives the same reference in APA and BibTeX, from
[CITATION.cff](CITATION.cff).

The data and the code are archived on Zenodo, with the DOI
[10.5281/zenodo.23265105](https://doi.org/10.5281/zenodo.23265105). This DOI always points to the
latest version.

## License

The code (`vn2_simulate.py`, `vn2_play.py`, `vn2_benchmark.py`) is under the [MIT license](LICENSE).
The data and the documentation are under [Creative Commons Attribution 4.0](LICENSE-DATA): use them
freely, and cite the competition as above.
