import csv
import os
from datetime import datetime

LOG_FILE = "whale_log.csv"

HEADERS = ["timestamp", "chain", "wallet", "action", "token", "amount_usd", "tx_hash", "explorer_url"]


def init_log():
    """Create CSV file with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
        print(f"[LOGGER] ✅ Log file created: {LOG_FILE}")


def log_transaction(chain, wallet, action, token, amount_usd, tx_hash, explorer_url):
    """Append a whale transaction to the CSV log."""
    row = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "chain": chain,
        "wallet": wallet,
        "action": action,
        "token": token,
        "amount_usd": round(amount_usd, 2),
        "tx_hash": tx_hash,
        "explorer_url": explorer_url
    }
    try:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writerow(row)
        print(f"[LOGGER] ✅ Logged: {chain} | {token} | ${amount_usd:,.0f}")
    except Exception as e:
        print(f"[LOGGER] ❌ Error logging: {e}")
