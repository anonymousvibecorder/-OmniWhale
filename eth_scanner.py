import requests
import time
from config import ETHERSCAN_API_KEY, ETHERSCAN_BASE, ETH_CHAIN_ID, WHALE_THRESHOLD, KNOWN_WALLETS
from telegram_alert import send_whale_alert
from logger import log_transaction

# Track last seen block to avoid duplicates
last_block_eth = 0

# ETH price cache
_eth_price = 0
_eth_price_time = 0


def get_eth_price():
    """Get current ETH price in USD."""
    global _eth_price, _eth_price_time
    now = time.time()
    if now - _eth_price_time < 60:
        return _eth_price
    try:
        url = f"{ETHERSCAN_BASE}?chainid={ETH_CHAIN_ID}&module=stats&action=ethprice&apikey={ETHERSCAN_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data["status"] == "1":
            _eth_price = float(data["result"]["ethusd"])
            _eth_price_time = now
            return _eth_price
    except Exception as e:
        print(f"[ETH] ❌ Price fetch error: {e}")
    return _eth_price or 3000  # fallback


def get_latest_block():
    """Get the latest Ethereum block number."""
    try:
        url = f"{ETHERSCAN_BASE}?chainid={ETH_CHAIN_ID}&module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return int(data["result"], 16)
    except Exception as e:
        print(f"[ETH] ❌ Block fetch error: {e}")
        return 0


def get_transactions(block_number):
    """Get normal transactions from the latest block."""
    try:
        url = (
            f"{ETHERSCAN_BASE}?chainid={ETH_CHAIN_ID}"
            f"&module=proxy&action=eth_getBlockByNumber"
            f"&tag={hex(block_number)}&boolean=true"
            f"&apikey={ETHERSCAN_API_KEY}"
        )
        r = requests.get(url, timeout=15)
        data = r.json()
        if data.get("result") and data["result"].get("transactions"):
            return data["result"]["transactions"]
    except Exception as e:
        print(f"[ETH] ❌ Transaction fetch error: {e}")
    return []


def get_token_transfers(block_number):
    """Get ERC-20 token transfers from the latest block via Etherscan."""
    try:
        url = (
            f"{ETHERSCAN_BASE}?chainid={ETH_CHAIN_ID}"
            f"&module=account&action=tokentx"
            f"&startblock={block_number}&endblock={block_number}"
            f"&address=0x0000000000000000000000000000000000000000"
            f"&page=1&offset=200&sort=desc"
            f"&apikey={ETHERSCAN_API_KEY}"
        )
        r = requests.get(url, timeout=15)
        data = r.json()

        # Etherscan tokentx requires an address, so we use an alternative approach:
        # Scan internal txs from the block instead. For token transfers, we parse
        # event logs for the Transfer event topic.
        url2 = (
            f"{ETHERSCAN_BASE}?chainid={ETH_CHAIN_ID}"
            f"&module=logs&action=getLogs"
            f"&fromBlock={block_number}&toBlock={block_number}"
            f"&topic0=0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            f"&page=1&offset=200"
            f"&apikey={ETHERSCAN_API_KEY}"
        )
        r2 = requests.get(url2, timeout=15)
        data2 = r2.json()
        if data2.get("status") == "1" and data2.get("result"):
            return data2["result"]
    except Exception as e:
        print(f"[ETH] ❌ Token transfer fetch error: {e}")
    return []


# Cache for token info (contract -> {symbol, decimals})
_token_cache = {}


def get_token_info(contract_address):
    """Get token symbol and decimals from Etherscan."""
    if contract_address in _token_cache:
        return _token_cache[contract_address]

    # Known stablecoins (hardcoded for speed, these are the big ones)
    KNOWN_ERC20 = {
        "0xdac17f958d2ee523a2206206994597c13d831ec7": {"symbol": "USDT", "decimals": 6, "price": 1.0},
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"symbol": "USDC", "decimals": 6, "price": 1.0},
        "0x6b175474e89094c44da98b954eedeac495271d0f": {"symbol": "DAI", "decimals": 18, "price": 1.0},
        "0x4fabb145d64652a948d72533023f6e7a623c7c53": {"symbol": "BUSD", "decimals": 18, "price": 1.0},
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {"symbol": "WBTC", "decimals": 8, "price": None},
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {"symbol": "WETH", "decimals": 18, "price": None},
        "0x514910771af9ca656af840dff83e8264ecf986ca": {"symbol": "LINK", "decimals": 18, "price": None},
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {"symbol": "UNI", "decimals": 18, "price": None},
        "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0": {"symbol": "MATIC", "decimals": 18, "price": None},
        "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce": {"symbol": "SHIB", "decimals": 18, "price": None},
        "0x6982508145454ce325ddbe47a25d4ec3d2311933": {"symbol": "PEPE", "decimals": 18, "price": None},
        "0xae78736cd615f374d3085123a210448e74fc6393": {"symbol": "rETH", "decimals": 18, "price": None},
        "0xbe9895146f7af43049ca1c1ae358b0541ea49704": {"symbol": "cbETH", "decimals": 18, "price": None},
        "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": {"symbol": "stETH", "decimals": 18, "price": None},
    }

    lower = contract_address.lower()
    if lower in KNOWN_ERC20:
        info = KNOWN_ERC20[lower]
        _token_cache[contract_address] = info
        return info

    # Fallback: unknown token
    _token_cache[contract_address] = {"symbol": "ERC20", "decimals": 18, "price": None}
    return _token_cache[contract_address]


def parse_token_transfer(log_entry, eth_price):
    """Parse a Transfer event log entry and return whale info if above threshold."""
    try:
        topics = log_entry.get("topics", [])
        if len(topics) < 3:
            return None

        contract = log_entry.get("address", "").lower()
        from_addr = "0x" + topics[1][-40:]
        to_addr = "0x" + topics[2][-40:]
        raw_value = int(log_entry.get("data", "0x0"), 16)

        token_info = get_token_info(contract)
        symbol = token_info["symbol"]
        decimals = token_info["decimals"]
        token_price = token_info.get("price")

        token_amount = raw_value / (10 ** decimals)

        # Calculate USD value
        if token_price is not None:
            value_usd = token_amount * token_price
        elif symbol == "WETH" or symbol == "stETH" or symbol == "rETH" or symbol == "cbETH":
            value_usd = token_amount * eth_price
        elif symbol == "WBTC":
            # Rough BTC estimate (we don't have BTC price, skip or use a multiplier)
            value_usd = token_amount * 90000  # rough fallback
        else:
            # Unknown token price — skip
            return None

        if value_usd < WHALE_THRESHOLD:
            return None

        tx_hash = log_entry.get("transactionHash", "")

        # Determine action
        action = "TOKEN TRANSFER"
        if from_addr.lower() in KNOWN_WALLETS:
            action = "TOKEN SELL (from exchange)"
        elif to_addr.lower() in KNOWN_WALLETS:
            action = "TOKEN BUY (to exchange)"

        wallet_label = KNOWN_WALLETS.get(from_addr.lower(), from_addr)
        explorer_url = f"https://etherscan.io/tx/{tx_hash}"

        return {
            "chain": "Ethereum",
            "wallet": wallet_label,
            "action": action,
            "token": symbol,
            "amount_usd": value_usd,
            "tx_hash": tx_hash,
            "explorer_url": explorer_url,
            "from": from_addr,
        }

    except Exception as e:
        return None


def scan_ethereum():
    """Scan Ethereum for whale transactions (native ETH + ERC-20 tokens)."""
    global last_block_eth

    print("[ETH] 🔍 Scanning Ethereum...")

    eth_price = get_eth_price()
    latest_block = get_latest_block()

    if latest_block == 0 or latest_block == last_block_eth:
        return

    transactions = get_transactions(latest_block)
    whale_count = 0

    # ── Native ETH transfers ──
    for tx in transactions:
        try:
            value_wei = int(tx.get("value", "0x0"), 16)
            value_eth = value_wei / 1e18
            value_usd = value_eth * eth_price

            if value_usd >= WHALE_THRESHOLD:
                whale_count += 1
                wallet = tx.get("from", "unknown")
                to_wallet = tx.get("to", "unknown")
                tx_hash = tx.get("hash", "")

                # Determine action label
                action = "TRANSFER"
                if wallet.lower() in KNOWN_WALLETS:
                    action = "SELL (from exchange)"
                elif to_wallet and to_wallet.lower() in KNOWN_WALLETS:
                    action = "BUY (to exchange)"

                # Label wallet if known
                wallet_label = KNOWN_WALLETS.get(wallet.lower(), wallet)
                explorer_url = f"https://etherscan.io/tx/{tx_hash}"

                print(f"[ETH] 🐋 WHALE: ${value_usd:,.0f} | {wallet_label} | {action}")

                send_whale_alert(
                    chain="Ethereum",
                    wallet=wallet_label,
                    action=action,
                    token="ETH",
                    amount_usd=value_usd,
                    tx_hash=tx_hash,
                    explorer_url=explorer_url
                )

                log_transaction(
                    chain="Ethereum",
                    wallet=wallet,
                    action=action,
                    token="ETH",
                    amount_usd=value_usd,
                    tx_hash=tx_hash,
                    explorer_url=explorer_url
                )

        except Exception as e:
            print(f"[ETH] ❌ TX parse error: {e}")
            continue

    # ── ERC-20 Token transfers ──
    seen_tx_hashes = set()
    token_logs = get_token_transfers(latest_block)
    token_whale_count = 0

    for log_entry in token_logs:
        result = parse_token_transfer(log_entry, eth_price)
        if result and result["tx_hash"] not in seen_tx_hashes:
            seen_tx_hashes.add(result["tx_hash"])
            token_whale_count += 1

            print(f"[ETH] 🪙 TOKEN WHALE: ${result['amount_usd']:,.0f} {result['token']} | {result['wallet']} | {result['action']}")

            send_whale_alert(
                chain="Ethereum",
                wallet=result["wallet"],
                action=result["action"],
                token=result["token"],
                amount_usd=result["amount_usd"],
                tx_hash=result["tx_hash"],
                explorer_url=result["explorer_url"]
            )

            log_transaction(
                chain="Ethereum",
                wallet=result["from"],
                action=result["action"],
                token=result["token"],
                amount_usd=result["amount_usd"],
                tx_hash=result["tx_hash"],
                explorer_url=result["explorer_url"]
            )

    last_block_eth = latest_block
    total_whales = whale_count + token_whale_count
    print(f"[ETH] ✅ Block {latest_block} | {len(transactions)} txs | {whale_count} ETH whales | {token_whale_count} token whales | ETH=${eth_price:,.0f}")
