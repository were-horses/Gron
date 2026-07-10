#!/usr/bin/env python3
"""
Telegram OTP Notifier - 24/7 Service
Run with: nohup python3 telegram_bot_daemon.py &
"""

import requests
import time
import json
import os
from datetime import datetime

# ===== CONFIGURATION =====
BOT_TOKEN = "7325597357:AAGt0t9u-5GHR6VOVdXFMdzNqAsT572lPBk"
CHAT_ID = "-1004290930965"
OTP_TOKEN = "MHBXC3CY7VB"
OTP_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp"
CHECK_INTERVAL = 10  # seconds
STATS_FILE = "otp_stats.json"
# =========================

def load_stats():
    """Load saved OTP IDs from file"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {"processed": []}

def save_stats(stats):
    """Save processed OTP IDs to file"""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)

def extract_sender(message):
    """Extract sender from OTP message"""
    import re
    patterns = [
        r'your\s+([A-Za-z0-9]+)\s+(?:code|verification|OTP)',
        r'from\s+([A-Za-z0-9]+)',
        r'for\s+([A-Za-z0-9]+)',
        r'([A-Za-z]+)\s+code',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return 'Unknown'

def send_telegram_message(otp):
    """Send OTP notification to Telegram"""
    message = f"""<blockquote>⏰ <b>Time:</b> {datetime.fromtimestamp(otp['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}</blockquote>
<blockquote>📌 <b>Sender:</b> {extract_sender(otp.get('message', ''))}</blockquote>
<blockquote>☎️ <b>Number:</b> {otp.get('number', 'Unknown')}</blockquote>

Panel - GENESYS SMS"""
    
    keyboard = {
        "inline_keyboard": [[
            {"text": "👨‍💻 Developer", "url": "https://t.me/prince_ACTIVE1"}
        ]]
    }
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": keyboard
            },
            timeout=10
        )
        return response.ok
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def fetch_otps():
    """Fetch OTPs from API"""
    try:
        response = requests.get(
            OTP_URL,
            headers={
                'mauthapi': OTP_TOKEN,
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('meta', {}).get('code') == 200:
                return data.get('data', {}).get('otps', [])
    except Exception as e:
        print(f"Fetch error: {e}")
    return []

def main():
    """Main loop"""
    print("=" * 60)
    print("🤖 Telegram OTP Notifier - 24/7 Service")
    print("=" * 60)
    print(f"📡 Checking every {CHECK_INTERVAL} seconds")
    print(f"📊 Stats file: {STATS_FILE}")
    print("Press Ctrl+C to stop\n")
    
    stats = load_stats()
    processed = set(stats.get("processed", []))
    total_sent = stats.get("total_sent", 0)
    
    print(f"📊 Already processed: {len(processed)} OTPs")
    
    try:
        while True:
            try:
                otps = fetch_otps()
                
                if otps:
                    # Check for new OTPs (reverse order - newest first)
                    new_otps = []
                    for otp in otps:
                        if otp.get('otp_id') not in processed:
                            new_otps.append(otp)
                            processed.add(otp.get('otp_id'))
                    
                    # Send new OTPs
                    for otp in new_otps[:5]:  # Limit to 5 per check
                        if send_telegram_message(otp):
                            total_sent += 1
                            print(f"✅ Sent: {otp.get('number')} - {otp.get('message', '')[:30]}...")
                            stats["processed"] = list(processed)
                            stats["total_sent"] = total_sent
                            save_stats(stats)
                        time.sleep(1)  # Avoid rate limiting
                    
                    if new_otps:
                        print(f"📤 Sent {len(new_otps)} new OTPs (Total: {total_sent})")
                else:
                    # Quiet mode - only print every 10 checks
                    if int(time.time()) % (CHECK_INTERVAL * 10) == 0:
                        print(f"⏳ No new OTPs - {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ Error in loop: {e}")
                time.sleep(CHECK_INTERVAL * 2)
                
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"🛑 Service stopped")
        print(f"📊 Total OTPs sent: {total_sent}")
        print(f"📊 Processed IDs: {len(processed)}")
        print("=" * 60)
        save_stats(stats)

if __name__ == "__main__":
    main()
