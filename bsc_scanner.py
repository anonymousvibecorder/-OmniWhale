import requests
import time
from config import WHALE_THRESHOLD, KNOWN_WALLETS, BSCSCAN_API_KEY
from telegram_alert import send_whale_alert
from logger import log_transaction

last_block_bsc = 0

_bnb_price = 0
_bnb_price_time = 0

# BscScan API base
BSCSCAN_BASE = "https://api.bscscan.com/api"

# Free public BSC RPC endpoint (no API key needed)
BSC_RPC = "https://bsc-dataseed.binance.org/"


def get_bnb_price():
    """Get current BNB price in USD from CoinGecko (free, no key needed)."""
    global _bnb_price, _bnb_price_time
    now = time.time()
    if now - _bnb_price_time < 60:
        return _bnb_price
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        _bnb_price = float(data["binancecoin"]["usd"])
        _bnb_price_time = now
        return _bnb_price
    except Exception as e:
        print(f"[BSC] ❌ Price fetch error: {e}")
    return _bnb_price or 600  # fallback


def rpc_call(method, params=None):
    """Make a JSON-RPC call to BSC public node."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or []
    }
    r = requests.post(BSC_RPC, json=payload, timeout=15)
    data = r.json()
    return data.get("result")


def get_latest_block_bsc():
    """Get the latest BSC block number."""
    try:
        result = rpc_call("eth_blockNumber")
        if result:
            return int(result, 16)
    except Exception as e:
        print(f"[BSC] ❌ Block fetch error: {e}")
    return 0


def get_bsc_transactions(block_number):
    """Get transactions from BSC block."""
    try:
        result = rpc_call("eth_getBlockByNumber", [hex(block_number), True])
        if result and result.get("transactions"):
            return result["transactions"]
    except Exception as e:
        print(f"[BSC] ❌ Transaction fetch error: {e}")
    return []


def get_bep20_transfers(block_number):
    """Get BEP-20 token Transfer event logs from the block via BscScan."""
    try:
        url = (
            f"{BSCSCAN_BASE}?module=logs&action=getLogs"
            f"&fromBlock={block_number}&toBlock={block_number}"
            f"&topic0=0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            f"&page=1&offset=200"
            f"&apikey={BSCSCAN_API_KEY}"
        )
        r = requests.get(url, timeout=15)
        data = r.json()
        if data.get("status") == "1" and data.get("result"):
            return data["result"]
    except Exception as e:
        print(f"[BSC] ❌ Token transfer fetch error: {e}")
    return []


# Known BEP-20 tokens on BSC
KNOWN_BEP20 = {
    "0x55d398326f99059ff775485246999027b3197955": {"symbol": "USDT", "decimals": 18, "price": 1.0},
    "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": {"symbol": "USDC", "decimals": 18, "price": 1.0},
    "0xe9e7cea3dedca5984780bafc599bd69add087d56": {"symbol": "BUSD", "decimals": 18, "price": 1.0},
    "0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3": {"symbol": "DAI", "decimals": 18, "price": 1.0},
    "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": {"symbol": "WBNB", "decimals": 18, "price": None},
    "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c": {"symbol": "BTCB", "decimals": 18, "price": None},
    "0x2170ed0880ac9a755fd29b2688956bd959f933f8": {"symbol": "ETH (BSC)", "decimals": 18, "price": None},
    "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82": {"symbol": "CAKE", "decimals": 18, "price": None},
    "0x3ee2200efb3400fabb9aacf31297cbdd1d435d47": {"symbol": "ADA (BSC)", "decimals": 18, "price": None},
    "0x1d2f0da169ceb9fc7b3144628db156f3f6c60dbe": {"symbol": "XRP (BSC)", "decimals": 18, "price": None},
}

_bep20_cache = {}


def get_bep20_info(contract_address):
    """Get BEP-20 token info."""
    if contract_address in _bep20_cache:
        return _bep20_cache[contract_address]

    lower = contract_address.lower()
    if lower in KNOWN_BEP20:
        info = KNOWN_BEP20[lower]
        _bep20_cache[contract_address] = info
        return info

    _bep20_cache[contract_address] = {"symbol": "BEP20", "decimals": 18, "price": None}
    return _bep20_cache[contract_address]


def parse_bep20_transfer(log_entry, bnb_price):
    """Parse a BEP-20 Transfer event log."""
    try:
        topics = log_entry.get("topics", [])
        if len(topics) < 3:
            return None

        contract = log_entry.get("address", "").lower()
        from_addr = "0x" + topics[1][-40:]
        to_addr = "0x" + topics[2][-40:]
        raw_value = int(log_entry.get("data", "0x0"), 16)

        token_info = get_bep20_info(contract)
        symbol = token_info["symbol"]
        decimals = token_info["decimals"]
        token_price = token_info.get("price")

        token_amount = raw_value / (10 ** decimals)

        if token_price is not None:
            value_usd = token_amount * token_price
        elif symbol == "WBNB":
            value_usd = token_amount * bnb_price
        elif symbol == "BTCB":
            value_usd = token_amount * 90000  # rough BTC fallback
        elif symbol == "ETH (BSC)":
            value_usd = token_amount * 3000  # rough ETH fallback
        else:
            return None

        if value_usd < WHALE_THRESHOLD:
            return None

        tx_hash = log_entry.get("transactionHash", "")

        action = "TOKEN TRANSFER"
        if from_addr.lower() in KNOWN_WALLETS:
            action = "TOKEN SELL (from exchange)"
        elif to_addr.lower() in KNOWN_WALLETS:
            action = "TOKEN BUY (to exchange)"

        wallet_label = KNOWN_WALLETS.get(from_addr.lower(), from_addr)
        explorer_url = f"https://bscscan.com/tx/{tx_hash}"

        return {
            "chain": "BNB Chain",
            "wallet": wallet_label,
            "action": action,
            "token": symbol,
            "amount_usd": value_usd,
            "tx_hash": tx_hash,
            "explorer_url": explorer_url,
            "from": from_addr,
        }
    except Exception:
        return None


def scan_bsc():
    """Scan BNB Chain for whale transactions (native BNB + BEP-20 tokens)."""
    global last_block_bsc

    print("[BSC] 🔍 Scanning BNB Chain...")

    bnb_price = get_bnb_price()
    latest_block = get_latest_block_bsc()

    if latest_block == 0 or latest_block == last_block_bsc:
        return

    transactions = get_bsc_transactions(latest_block)
    whale_count = 0

    # ── Native BNB transfers ──
    for tx in transactions:
        try:
            value_wei = int(tx.get("value", "0x0"), 16)
            value_bnb = value_wei / 1e18
            value_usd = value_bnb * bnb_price

            if value_usd >= WHALE_THRESHOLD:
                whale_count += 1
                wallet = tx.get("from", "unknown")
                to_wallet = tx.get("to", "unknown")
                tx_hash = tx.get("hash", "")

                action = "TRANSFER"
                if wallet.lower() in KNOWN_WALLETS:
                    action = "SELL (from exchange)"
                elif to_wallet and to_wallet.lower() in KNOWN_WALLETS:
                    action = "BUY (to exchange)"

                wallet_label = KNOWN_WALLETS.get(wallet.lower(), wallet)
                explorer_url = f"https://bscscan.com/tx/{tx_hash}"

                print(f"[BSC] 🐋 WHALE: ${value_usd:,.0f} | {wallet_label} | {action}")

                send_whale_alert(
                    chain="BNB Chain",
                    wallet=wallet_label,
                    action=action,
                    token="BNB",
                    amount_usd=value_usd,
                    tx_hash=tx_hash,
                    explorer_url=explorer_url
                )

                log_transaction(
                    chain="BNB Chain",
                    wallet=wallet,
                    action=action,
                    token="BNB",
                    amount_usd=value_usd,
                    tx_hash=tx_hash,
                    explorer_url=explorer_url
                )

        except Exception as e:
            print(f"[BSC] ❌ TX parse error: {e}")
            continue

    # ── BEP-20 Token transfers ──
    seen_tx_hashes = set()
    token_logs = get_bep20_transfers(latest_block)
    token_whale_count = 0

    for log_entry in token_logs:
        result = parse_bep20_transfer(log_entry, bnb_price)
        if result and result["tx_hash"] not in seen_tx_hashes:
            seen_tx_hashes.add(result["tx_hash"])
            token_whale_count += 1

            print(f"[BSC] 🪙 TOKEN WHALE: ${result['amount_usd']:,.0f} {result['token']} | {result['wallet']} | {result['action']}")

            send_whale_alert(
                chain="BNB Chain",
                wallet=result["wallet"],
                action=result["action"],
                token=result["token"],
                amount_usd=result["amount_usd"],
                tx_hash=result["tx_hash"],
                explorer_url=result["explorer_url"]
            )

            log_transaction(
                chain="BNB Chain",
                wallet=result["from"],
                action=result["action"],
                token=result["token"],
                amount_usd=result["amount_usd"],
                tx_hash=result["tx_hash"],
                explorer_url=result["explorer_url"]
            )

    last_block_bsc = latest_block
    total_whales = whale_count + token_whale_count
    print(f"[BSC] ✅ Block {latest_block} | {len(transactions)} txs | {whale_count} BNB whales | {token_whale_count} token whales | BNB=${bnb_price:,.0f}")
