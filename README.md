<div align="center">
  
# 🐋 OmniWhale
**Real-Time Multi-Chain Smart Money & Whale Tracker**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ethereum](https://img.shields.io/badge/Ethereum-Supported-3C3C3D.svg?logo=ethereum)](https://ethereum.org/)
[![Binance Smart Chain](https://img.shields.io/badge/BSC-Supported-F3BA2F.svg?logo=binance)](https://www.binance.org/)
[![Solana](https://img.shields.io/badge/Solana-Supported-14F195.svg?logo=solana)](https://solana.com/)

An enterprise-grade, lightweight on-chain analytics bot that monitors Ethereum, BNB Chain, and Solana in real-time. OmniWhale detects massive liquidity movements, native coin transfers, and token swaps (ERC-20, BEP-20, SPL) exceeding user-defined thresholds. By cross-referencing transactions against an internal database of known exchange hot wallets, DeFi protocols, and market makers, OmniWhale delivers instantaneous Alpha directly to your Telegram.

</div>

---

## ✨ Features

- **Multi-Chain Native Support**: Scans Ethereum (ETH), BNB Chain (BSC), and Solana (SOL) block-by-block.
- **Deep Token Tracking**: Doesn't just track native gas tokens—fully resolves ERC-20, BEP-20, and SPL token transfers mapping them to real-time USD values.
- **Smart Wallet Labeling**: Built-in database of ~50 major entities including Binance, OKX, Coinbase, Kraken, Lido, Uniswap, Jump Trading, and Wintermute.
- **Trade Context**: Automatically categorizes transactions as `Transfer`, `Exchange Deposit (Sell Pressure)`, or `Exchange Withdrawal (Accumulation)`.
- **Instant Telegram Alerts**: Get notified the second a multi-million-dollar transaction hits the blockchain.
- **Automated CSV Logging**: Keeps a local database (`whale_log.csv`) of all detected whale movements for backtesting and historical analysis.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8 or higher
- Free API keys from [Etherscan](https://etherscan.io/apis), [BscScan](https://bscscan.com/apis), and [Helius](https://dev.helius.xyz/) (for Solana).
- A Telegram Bot Token and Chat ID.

### 2. Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/OmniWhale.git
cd OmniWhale
pip install -r requirements.txt
```

### 3. Configuration

**⚠️ IMPORTANT:** Never commit your real `.env` file to GitHub! The repository includes a `.gitignore` specifically to protect it.

1. Copy the example environment file to create your real one:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and configure your API keys and Telegram settings:

   ```env
   # Etherscan V2 API Key (ETH)
   ETHERSCAN_API_KEY=your_etherscan_api_key_here
   
   # BscScan API Key (get free at https://bscscan.com/apis)
   BSCSCAN_API_KEY=your_bscscan_api_key_here
   
   # Helius API Key (Solana) (get free at https://dev.helius.xyz/)
   HELIUS_API_KEY=your_helius_api_key_here
   
   # Telegram Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   
   # Target transaction size in USD to trigger an alert
   WHALE_THRESHOLD=500000
   
   # Wait time between full cycle scans (in seconds)
   POLL_INTERVAL=30
   ```

### 4. Run the Tracker

```bash
python main.py
```

---

## 📱 Telegram Alert Format

When OmniWhale detects a massive transaction, you'll receive a beautifully formatted alert:

```
🐋 WHALE ALERT
━━━━━━━━━━━━━━━━━━━
Chain    : Ethereum
Wallet   : Wintermute
Action   : TOKEN BUY (to exchange)
Token    : USDT
Amount   : $2,400,000
Time     : 14:23 UTC
Explorer : https://etherscan.io/tx/...
━━━━━━━━━━━━━━━━━━━
```

## 🧠 Why Use OmniWhale? (The Alpha)

Following the "Smart Money" is one of the most effective strategies in crypto. OmniWhale is designed to give you edge by:
1. **Detecting Early Accumulation**: Watch for massive token withdrawals from exchanges into cold storage.
2. **Front-Running Sell Pressure**: Get alerted when market makers or whales deposit millions of a specific token to exchange hot wallets before they hit the order books.
3. **Discovering New Narratives**: See what obscure tokens whales are interacting with on-chain before CT (Crypto Twitter) finds out.

## 🤝 Contributing

Contributions are welcome! If you want to add support for new chains (Arbitrum, Base, Polygon), expand the known wallet database, or integrate DEX router tracking, please open a PR.

## 📝 License

This project is open-sourced under the MIT License.
