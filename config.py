import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", os.getenv("ETHERSCAN_API_KEY"))
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Settings
WHALE_THRESHOLD = int(os.getenv("WHALE_THRESHOLD", 500000))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 30))

# API Endpoints
ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"
BSCSCAN_BASE   = "https://api.bscscan.com/api"
HELIUS_BASE    = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# Chain ID for Etherscan V2 (ETH only)
ETH_CHAIN_ID = 1

# Known exchange/whale wallets (label map) — EVM chains (ETH & BSC)
KNOWN_WALLETS = {
    # ── Binance ──
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Cold Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance US",
    "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance Whale",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance Cold 2",
    "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance Hot 2",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance Cold 3",
    "0x3c783c21a0383057d128bae431894a5c19f9cf06": "Binance Cold 4",
    "0xb1a2bc2ec50000fbb26b01b6a9a60a5347862e1e": "Binance Staking",
    # ── OKX ──
    "0x0716a17fbaee714f1e6ab0f9d59edbc5f09815c0": "OKX Exchange",
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX Hot Wallet",
    "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": "OKX Cold Wallet",
    # ── Coinbase ──
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "Coinbase Cold",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase Hot",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase Cold 2",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase Cold 3",
    "0x3cd751e6b0078be393132286c442345e68ff0aab": "Coinbase Cold 4",
    # ── Kraken ──
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken Hot Wallet",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken Cold Wallet",
    "0x53d284357ec70ce289d6d64134dfac8e511c8a3d": "Kraken Cold 2",
    "0x89e51fa8ca5d66cd220baed62ed01e8951aa7c40": "Kraken Hot 2",
    # ── Bybit ──
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit Hot Wallet",
    "0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4": "Bybit Cold Wallet",
    # ── KuCoin ──
    "0xd6216fc19db775df9774a6e33526131da7d19a2c": "KuCoin Hot Wallet",
    "0xeb2d2f1b8c558a40b2955bcc9153ef8c7b5c7e42": "KuCoin Cold Wallet",
    "0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91": "KuCoin Hot 2",
    # ── Gate.io ──
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io Hot Wallet",
    "0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c": "Gate.io Cold Wallet",
    # ── Bitfinex ──
    "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa": "Bitfinex Hot Wallet",
    "0x742d35cc6634c0532925a3b844bc9e7595f2bd1e": "Bitfinex Cold Wallet",
    "0xc6cde7c39eb2f0f0095f41570af89efc2c1ea828": "Bitfinex Cold 2",
    # ── Gemini ──
    "0xd24400ae8bfebb18ca49be86258a3c749cf46853": "Gemini Hot Wallet",
    "0x6fc82a5fe25a5cdb58bc74600a40a69c065263f8": "Gemini Cold Wallet",
    # ── Crypto.com ──
    "0x6262998ced04146fa42253a5c0af90ca02dfd2a3": "Crypto.com Hot Wallet",
    "0x46340b20830761efd32832a74d7169b29feb9758": "Crypto.com Cold Wallet",
    # ── HTX (Huobi) ──
    "0xab5c66752a9e8167967685f1450532fb96d5d24f": "HTX (Huobi) Cold",
    "0x6748f50f686bfbca6fe7e82164a6c7ca1207e076": "HTX (Huobi) Hot",
    "0x18709e89bd403f470088abdacebe86cc60dda12e": "HTX (Huobi) Hot 2",
    # ── DeFi Protocols ──
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": "Uniswap Treasury",
    "0x47173b170c64d16393a52e6c480b3ad8c302ba1e": "Lido Finance",
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": "Lido stETH Contract",
    "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": "Aave V2 Lending Pool",
    "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": "Aave V3 Pool",
    "0x9aa99c23f67c81701c772b106b4f83b6e0a26998": "Curve Finance",
    "0x5a52e96bacdabb82fd05763e25335261b270efcb": "MakerDAO",
    "0xc3d688b66703497daa19211eedff47f25384cdc3": "Compound V3 (USDC)",
    # ── Market Makers / Funds ──
    "0xf584f8728b874a6a5c7a8d4d387c9aae9172d621": "Jump Trading",
    "0x0000006daea1723962647b7e189d311d757fb793": "Wintermute",
    "0x4862733b5fddfd35f35ea8ccf08f5045e57388b3": "Wintermute 2",
    "0x93c08a3168fc469f3fc165cd3a471d19a15c2e92": "Alameda Research (Legacy)",
    "0x56178a0d5f301baf6cf3e1cd53d9863437345bf9": "Celsius (Legacy)",
    "0x8103683202aa8da10536036edef04cdd865c225e": "Galaxy Digital",
}

# ── Solana-specific wallet labels ──
KNOWN_SOL_WALLETS = {
    # Exchanges
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "Binance SOL Hot",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "Binance SOL Cold",
    "2ojv9BAiHUrvsm9gxDe7fJSzbNZSJcxZvf8dqmWGHG8S": "Bybit SOL",
    "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE": "Coinbase SOL",
    "4rXJczEJJCJbxnEP7bYBECnmWkGsvdAF4ARpew3HJvkX": "Kraken SOL",
    "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH": "OKX SOL",
    # Market Makers
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter Exchange",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Whirlpool",
}

# ── Known SPL token mints (Solana) ──
KNOWN_SOL_TOKENS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
    "So11111111111111111111111111111111111111112": "WSOL",
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": "JUP",
    "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL": "JTO",
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",
    "WENWENvqqNya429ubCdR81ZmD69brwQaaBYY6p3LCpk": "WEN",
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": "WETH (Solana)",
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": "mSOL",
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn": "jitoSOL",
    "RLBxxFkseAZ4RgJH3Sqn8jXxhmGoz9jWxDNJMh8pL7a": "RLBB",
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": "POPCAT",
    "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof": "RENDER",
}

