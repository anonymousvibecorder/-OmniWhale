import time
import sys
from config import POLL_INTERVAL, WHALE_THRESHOLD
from telegram_alert import send_startup_message
from logger import init_log
from eth_scanner import scan_ethereum
from bsc_scanner import scan_bsc
from sol_scanner import scan_solana


def run():
    print("=" * 50)
    print("  🐋 CRYPTO WHALE SCANNER")
    print("=" * 50)
    print(f"  Threshold : ${WHALE_THRESHOLD:,}")
    print(f"  Interval  : {POLL_INTERVAL}s")
    print(f"  Chains    : ETH | BSC | SOL")
    print("=" * 50)

    # Init CSV log
    init_log()

    # Send startup Telegram message
    send_startup_message()

    cycle = 0

    while True:
        cycle += 1
        print(f"\n[MAIN] ── Cycle {cycle} ──────────────────────────")

        try:
            scan_ethereum()
        except Exception as e:
            print(f"[MAIN] ❌ ETH scanner error: {e}")

        time.sleep(2)  # small delay between chain scans to respect rate limits

        try:
            scan_bsc()
        except Exception as e:
            print(f"[MAIN] ❌ BSC scanner error: {e}")

        time.sleep(2)

        try:
            scan_solana()
        except Exception as e:
            print(f"[MAIN] ❌ SOL scanner error: {e}")

        print(f"[MAIN] ⏳ Sleeping {POLL_INTERVAL}s...\n")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[MAIN] 🛑 Scanner stopped by user.")
        sys.exit(0)
