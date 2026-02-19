import requests
import os
import smtplib
import json
import time
from email.mime.text import MIMEText

# --- CONFIG ---
URL = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
COOLDOWN_SECONDS = 3600  # 1 hour
STATE_FILE = "last_alert.json"

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD") 
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

TARGET_ZONES = [
    {"target": 2650.50, "pips": 2},
    {"target": 2610.00, "pips": 5}
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def send_alert(price, target):
    msg = MIMEText(f"Gold Alert! Price: {price} is near {target}.")
    msg['Subject'] = f"GOLD ALERT: {price}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

def check_price():
    state = load_state()
    try:
        response = requests.get(URL, timeout=10)
        data = response.json()[0]
        current_price = (data['bidPrice'] + data['askPrice']) / 2
        print(f"Gold: {current_price}")

        for zone in TARGET_ZONES:
            target = str(zone['target'])
            buffer = zone['pips'] * 0.01
            
            if (zone['target'] - buffer) <= current_price <= (zone['target'] + buffer):
                last_sent = state.get(target, 0)
                # Only send if cooldown has passed
                if time.time() - last_sent > COOLDOWN_SECONDS:
                    send_alert(current_price, zone['target'])
                    state[target] = time.time()
                    print(f"Alert sent for {target}")
                else:
                    print(f"In zone for {target}, but on cooldown.")
        
        save_state(state)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_price()
