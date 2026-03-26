import requests
import time
from config import HELIUS_BASE, WHALE_THRESHOLD, KNOWN_SOL_WALLETS, KNOWN_SOL_TOKENS
from telegram_alert import send_whale_alert
from logger import log_transaction

last_slot = 0

_sol_price = 0
_sol_price_time = 0


def get_sol_price():
    """Get current SOL price from CoinGecko (free, no key needed)."""
    global _sol_price, _sol_price_time
    now = time.time()
    if now - _sol_price_time < 60:
        return _sol_price
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        _sol_price = float(data["solana"]["usd"])
        _sol_price_time = now
        return _sol_price
    except Exception as e:
        print(f"[SOL] ❌ Price fetch error: {e}")
    return _sol_price or 150  # fallback


def get_latest_slot():
    """Get the latest Solana slot."""
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
        r = requests.post(HELIUS_BASE, json=payload, timeout=10)
        data = r.json()
        return data.get("result", 0)
    except Exception as e:
        print(f"[SOL] ❌ Slot fetch error: {e}")
        return 0


def get_block_transactions(slot):
    """Get transactions for a Solana block/slot."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlock",
            "params": [
                slot,
                {
                    "encoding": "jsonParsed",
                    "maxSupportedTransactionVersion": 0,
                    "transactionDetails": "full",
                    "rewards": False
                }
            ]
        }
        r = requests.post(HELIUS_BASE, json=payload, timeout=15)
        data = r.json()
        if "result" in data and data["result"] and "transactions" in data["result"]:
            return data["result"]["transactions"]
    except Exception as e:
        print(f"[SOL] ❌ Block fetch error: {e}")
    return []


def get_wallet_label(address):
    """Get Solana wallet label if known."""
    return KNOWN_SOL_WALLETS.get(address, address)


def extract_sol_transfer(tx):
    """Extract SOL transfer amount from a transaction."""
    try:
        meta = tx.get("meta", {})
        if meta.get("err"):
            return None, None, None

        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])

        if not pre_balances or not post_balances:
            return None, None, None

        # Calculate the largest balance change (sender)
        max_change = 0
        sender_index = 0
        for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
            change = abs(pre - post) / 1e9  # lamports to SOL
            if change > max_change:
                max_change = change
                sender_index = i

        account_keys = tx.get("transaction", {}).get("message", {}).get("accountKeys", [])
        sender = None
        if account_keys and sender_index < len(account_keys):
            key = account_keys[sender_index]
            sender = key.get("pubkey") if isinstance(key, dict) else str(key)

        sig_list = tx.get("transaction", {}).get("signatures", [])
        tx_hash = sig_list[0] if sig_list else "unknown"

        return max_change, sender, tx_hash

    except Exception as e:
        print(f"[SOL] ❌ Parse error: {e}")
        return None, None, None


def extract_spl_transfers(tx, sol_price):
    """Extract SPL token transfers from a transaction."""
    results = []
    try:
        meta = tx.get("meta", {})
        if meta.get("err"):
            return results

        pre_token = meta.get("preTokenBalances", [])
        post_token = meta.get("postTokenBalances", [])

        if not pre_token and not post_token:
            return results

        sig_list = tx.get("transaction", {}).get("signatures", [])
        tx_hash = sig_list[0] if sig_list else "unknown"

        account_keys = tx.get("transaction", {}).get("message", {}).get("accountKeys", [])

        # Build a map of account index -> token balance changes
        pre_map = {}
        for bal in pre_token:
            idx = bal.get("accountIndex", -1)
            mint = bal.get("mint", "")
            amount = float(bal.get("uiTokenAmount", {}).get("uiAmount") or 0)
            pre_map[(idx, mint)] = amount

        post_map = {}
        for bal in post_token:
            idx = bal.get("accountIndex", -1)
            mint = bal.get("mint", "")
            amount = float(bal.get("uiTokenAmount", {}).get("uiAmount") or 0)
            post_map[(idx, mint)] = amount

        # Find all mints involved
        all_keys = set(list(pre_map.keys()) + list(post_map.keys()))
        mint_changes = {}

        for key in all_keys:
            idx, mint = key
            pre_amt = pre_map.get(key, 0)
            post_amt = post_map.get(key, 0)
            change = abs(post_amt - pre_amt)

            if change > 0:
                if mint not in mint_changes or change > mint_changes[mint]["change"]:
                    # Get owner from pre or post token balances
                    owner = None
                    for bal_list in [pre_token, post_token]:
                        for bal in bal_list:
                            if bal.get("mint") == mint and bal.get("accountIndex") == idx:
                                owner = bal.get("owner")
                                break
                        if owner:
                            break

                    mint_changes[mint] = {
                        "change": change,
                        "owner": owner,
                        "idx": idx,
                    }

        for mint, info in mint_changes.items():
            token_symbol = KNOWN_SOL_TOKENS.get(mint, None)

            # Calculate USD value
            if token_symbol in ("USDC", "USDT"):
                value_usd = info["change"]
            elif token_symbol in ("WSOL", "mSOL", "jitoSOL"):
                value_usd = info["change"] * sol_price
            elif token_symbol == "WETH (Solana)":
                value_usd = info["change"] * 3000  # rough ETH fallback
            elif token_symbol:
                # Known token but no price — skip
                continue
            else:
                # Unknown token — skip
                continue

            if value_usd < WHALE_THRESHOLD:
                continue

            owner = info["owner"] or "unknown"
            wallet_label = get_wallet_label(owner)

            # Determine action
            action = "TOKEN TRANSFER"
            if owner in KNOWN_SOL_WALLETS:
                action = "TOKEN SELL (from exchange)"

            results.append({
                "chain": "Solana",
                "wallet": wallet_label,
                "action": action,
                "token": token_symbol,
                "amount_usd": value_usd,
                "tx_hash": tx_hash,
                "explorer_url": f"https://solscan.io/tx/{tx_hash}",
                "owner": owner,
            })

    except Exception as e:
        print(f"[SOL] ❌ SPL parse error: {e}")

    return results


def scan_solana():
    """Scan Solana for whale transactions (native SOL + SPL tokens)."""
    global last_slot

    print("[SOL] 🔍 Scanning Solana...")

    sol_price = get_sol_price()
    latest_slot = get_latest_slot()

    if latest_slot == 0 or latest_slot == last_slot:
        return

    # Scan slightly behind latest to ensure block is finalized
    scan_slot = latest_slot - 5
    if scan_slot <= last_slot:
        return

    transactions = get_block_transactions(scan_slot)
    whale_count = 0
    token_whale_count = 0

    for tx in transactions:
        try:
            # ── Native SOL transfers ──
            sol_amount, sender, tx_hash = extract_sol_transfer(tx)

            if sol_amount is not None:
                value_usd = sol_amount * sol_price

                if value_usd >= WHALE_THRESHOLD:
                    whale_count += 1
                    explorer_url = f"https://solscan.io/tx/{tx_hash}"
                    wallet_label = get_wallet_label(sender or "unknown")

                    action = "TRANSFER"
                    if sender and sender in KNOWN_SOL_WALLETS:
                        action = "SELL (from exchange)"

                    print(f"[SOL] 🐋 WHALE: ${value_usd:,.0f} | {wallet_label[:20]}... | {action}")

                    send_whale_alert(
                        chain="Solana",
                        wallet=wallet_label,
                        action=action,
                        token="SOL",
                        amount_usd=value_usd,
                        tx_hash=tx_hash,
                        explorer_url=explorer_url
                    )

                    log_transaction(
                        chain="Solana",
                        wallet=sender or "unknown",
                        action=action,
                        token="SOL",
                        amount_usd=value_usd,
                        tx_hash=tx_hash,
                        explorer_url=explorer_url
                    )

            # ── SPL Token transfers ──
            spl_results = extract_spl_transfers(tx, sol_price)
            for result in spl_results:
                token_whale_count += 1

                print(f"[SOL] 🪙 TOKEN WHALE: ${result['amount_usd']:,.0f} {result['token']} | {result['wallet'][:20]}... | {result['action']}")

                send_whale_alert(
                    chain="Solana",
                    wallet=result["wallet"],
                    action=result["action"],
                    token=result["token"],
                    amount_usd=result["amount_usd"],
                    tx_hash=result["tx_hash"],
                    explorer_url=result["explorer_url"]
                )

                log_transaction(
                    chain="Solana",
                    wallet=result["owner"],
                    action=result["action"],
                    token=result["token"],
                    amount_usd=result["amount_usd"],
                    tx_hash=result["tx_hash"],
                    explorer_url=result["explorer_url"]
                )

        except Exception as e:
            print(f"[SOL] ❌ TX error: {e}")
            continue

    last_slot = scan_slot
    print(f"[SOL] ✅ Slot {scan_slot} | {len(transactions)} txs | {whale_count} SOL whales | {token_whale_count} token whales | SOL=${sol_price:,.0f}")
