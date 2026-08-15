
import random
import csv


def main():
    print("starting to save dummy data...")
    data_array = create_dummy_data()
    save_dummy_data(data_array)


def create_dummy_data():
    symbols = ["GOLD", "NQ", "ES", "CL", "NG"]
    exit_reasons = ["TP", "SL", "MANUAL"]
    directions = ["LONG", "SHORT"]
    price_ranges = {
        "GOLD": (1800, 2000),
        "NQ": (12000, 15000),
        "ES": (4000, 5000),
        "CL": (60, 80),
        "NG": (2, 4),
    }
    total = 200
    # ensure at least 52% wins
    min_wins = int(total * 0.52 + 0.999)

    data_array = []

    # create a list of booleans indicating whether each trade is a win
    wins = [True] * min_wins + [False] * (total - min_wins)
    random.shuffle(wins)

    seen = set()
    for i in range(total):
        symbol = random.choice(symbols)
        direction = random.choice(directions)
        exit_reason = random.choice(exit_reasons)
        entry_price = random.uniform(*price_ranges[symbol])

        # Determine exit_price to guarantee win/loss according to wins list
        # use a small delta relative to price range to make prices realistic
        low, high = price_ranges[symbol]
        delta = (high - low) * random.uniform(0.002, 0.02)
        is_win = wins[i]

        if direction == "LONG":
            if is_win:
                exit_price = entry_price + delta
                exit_reason = exit_reason if exit_reason != "SL" else "TP"
            else:
                exit_price = entry_price - delta
                exit_reason = exit_reason if exit_reason != "TP" else "SL"
            profit_loss = exit_price - entry_price
        else:  # SHORT
            if is_win:
                exit_price = entry_price - delta
                exit_reason = exit_reason if exit_reason != "SL" else "TP"
            else:
                exit_price = entry_price + delta
                exit_reason = exit_reason if exit_reason != "TP" else "SL"
            profit_loss = entry_price - exit_price

        # ensure uniqueness (simple retry with small jitter)
        key = (symbol, round(entry_price, 6), round(exit_price, 6), direction)
        retry = 0
        while key in seen and retry < 5:
            entry_price += random.uniform(-delta, delta)
            if direction == "LONG":
                exit_price = entry_price + (delta if is_win else -delta)
            else:
                exit_price = entry_price - (delta if is_win else -delta)
            profit_loss = (exit_price - entry_price) if direction == "LONG" else (entry_price - exit_price)
            key = (symbol, round(entry_price, 6), round(exit_price, 6), direction)
            retry += 1

        seen.add(key)

        data_array.append([
            symbol,
            exit_reason,
            entry_price,      # entry_price
            exit_price,       # exit_price
            profit_loss,      # profit_loss
            direction,        # direction
            random.uniform(100, 500),     # stop_loss
            random.uniform(500, 1500),    # take_profit
            random.uniform(1, 10),         # lots
            random.uniform(0.5, 2.0),     # duration
            random.uniform(0.5, 2.0),     # max_dd_during_trade
            random.uniform(0.1, 1.0),     # spread_at_entry
        ])
    print(f"created {len(data_array)} dummy data entries")
    return data_array


def save_dummy_data(data_array):
    header = [
        "symbol",
        "exit_reason",
        "entry_price",
        "exit_price",
        "profit_loss",
        "stop_loss",
        "take_profit",
        "lots",
        "duration",
        "max_dd_during_trade",
        "spread_at_entry",
    ]

    with open("dummy_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_array)

    print("dummy data saved to dummy_data.csv")


if __name__ == "__main__":
    main()