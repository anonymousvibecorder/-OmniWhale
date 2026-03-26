import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_whale_alert(chain, wallet, action, token, amount_usd, tx_hash, explorer_url):
    """Send a whale alert to Telegram."""
    now = datetime.utcnow().strftime("%H:%M UTC")

    # Shorten wallet for display
    short_wallet = f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) > 10 else wallet

    message = (
        f"🐋 *WHALE ALERT*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Chain    : `{chain}`\n"
        f"Wallet   : `{short_wallet}`\n"
        f"Action   : *{action}*\n"
        f"Token    : `{token}`\n"
        f"Amount   : *${amount_usd:,.0f}*\n"
        f"Time     : {now}\n"
        f"Explorer : {explorer_url}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[TELEGRAM] ✅ Alert sent: {chain} | {token} | ${amount_usd:,.0f}")
        else:
            print(f"[TELEGRAM] ❌ Failed: {response.text}")
    except Exception as e:
        print(f"[TELEGRAM] ❌ Error: {e}")


def send_startup_message():
    """Send a startup notification."""
    message = (
        "🚀 *Whale Scanner Started*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✅ Ethereum — Active\n"
        "✅ BNB Chain — Active\n"
        "✅ Solana — Active\n"
        f"🎯 Threshold: $500,000+\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Monitoring for whale transactions..."
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("[TELEGRAM] ✅ Startup message sent")
    except Exception as e:
        print(f"[TELEGRAM] ❌ Startup message error: {e}")
