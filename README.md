# sakas.in

Home page of the YouTube channel **saka's corner** ([@sakascorner](https://www.youtube.com/@sakascorner)).

## What updates by itself, and what you update

| What | Who | File |
|---|---|---|
| Video list | automatic, every day (YouTube feed) | `videos.json` |
| Petrol & diesel: Chennai, Delhi, Mumbai, Kolkata | automatic, every day (PPAC, Govt of India) | `data/fuel-daily.csv` |
| Gold 22K, gold 24K, silver (Chennai) | **you**, daily | `data/metals-daily.csv` |
| Auto-LPG, Trichy (shown as "Trichy live price") | automatic, every day (KR Fuels website, krfuels.com) | `data/autolpg-daily.csv` |
| LPG cylinder, CNG | **you**, monthly | `data/fuel-monthly.csv` |
| The price board on the site (now / 1 / 3 / 5 years ago) | automatic, built from the three files above | `prices.json` (don't edit) |

The automatic part runs on GitHub every morning at 06:00 IST and again a minute after you save a file in `data/`
(see the **Actions** tab; "Run workflow" runs it now). Your computer doesn't need to be on.

## Adding your prices (on GitHub)

Open the file → pencil icon (**Edit**) → add a line at the bottom → **Commit changes**. The site updates in 1–2 minutes.

**Gold & silver, daily** – `data/metals-daily.csv`, one line per day:
```
2026-11-22,11500,12545,165000
```
date (YYYY-MM-DD), gold 22K per gram, gold 24K per gram, silver per kg. Leave a value empty (`2026-11-22,11500,,`) if you don't have it.
To show 1, 3 and 5 years ago from the start, add lines for those dates too (e.g. `2025-11-22,...`, `2023-11-22,...`, `2021-11-22,...`).

**LPG, CNG, Auto-LPG, monthly** – `data/fuel-monthly.csv`, one line per month:
```
2026-11,957.50,99.50,
```
month (YYYY-MM), LPG cylinder, CNG per kg, Auto-LPG per litre, where the Auto-LPG price is from (empty = not known).

**Auto-LPG** has no reliable website, so use the pump price at KR Fuels (board or bill): Chennai if available,
otherwise Trichy. Write the place in the last column, **without commas**:
```
2026-11,957.50,99.50,62.00,KR Fuels Chennai
2026-11,957.50,99.50,62.00,KR Fuels Trichy
```
The site shows the place under Auto-LPG. Comparisons (1 / 3 / 5 years ago) only use history from the same city:
a Chennai price is compared with earlier Chennai prices (lines with no place count as Chennai), a Trichy price only
with earlier Trichy lines. So a Trichy price shows "no data" for the past until you add older Trichy lines.

Rules: numbers only (no ₹, no commas), dates as shown, one line per date. A line with a mistake is skipped, not fatal.
An item whose newest value is too old (over 45 days for daily, over 100 days for monthly) is hidden until you add a newer line.

## Looking up a past price

The three files in `data/` are the full history: open one on GitHub to see it as a table (with search), or download it
and open it in Excel. Petrol & diesel go back to 16 June 2017 (every day); LPG, CNG and Auto-LPG to 2021 (monthly).
In `fuel-daily.csv`, `petrol_per_litre` / `diesel_per_litre` are Chennai; the other metros have their own columns
(`delhi_petrol_per_litre`, `mumbai_diesel_per_litre`, ...). On the site, visitors pick the city for petrol and diesel
(the choice is remembered on their phone and shared with the calculator); everything else is Chennai.

## Other files

- `index.html` – the home page. `calculator/` – Taxi Wallet Calculator (https://sakas.in/calculator/).
- `scripts/` – the small programs GitHub runs (`update_videos.py`, `update_fuel.py`, `build_prices.py`).
- `CNAME` – the custom domain (sakas.in).
