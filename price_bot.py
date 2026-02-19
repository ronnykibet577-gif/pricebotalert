import requests
import os
import smtplib
import json
import time
from email.mime.text import MIMEText

# --- CONFIG ---
URL = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
COOLDOWN_SECONDS = 3600  
STATE_FILE = "last_alert.json"

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD") 
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# Target Prices & Pip Zones (1 pip in Gold = 0.01)
# Note: Gold is currently around 4200 in your data snippet
TARGET_ZONES = [
    {"target": 4213.00, "pips": 10}, 
    {"target": 4300.00, "pips": 5},
    {"target": 4863.00, "pips": 10},
    {"target": 4758.00, "pips": 10}
]

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def send_alert(price, target):
    msg = MIMEText(f"Gold Alert Triggered!\n\nCurrent Price: {price}\nTarget Zone: {target}")
    msg['Subject'] = f"XAU/USD ALERT: {price}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"Email sent successfully for {price}")
    except Exception as e:
        print(f"Email error: {e}")

def check_price():
    state = load_state()
    try:
        response = requests.get(URL, timeout=15)
        data = response.json()
        
        # NAVIGATION: First platform -> first spread profile
        first_platform = data[0]
        prices = first_platform['spreadProfilePrices'][0]
        
        bid = float(prices['bid'])
        ask = float(prices['ask'])
        current_price = (bid + ask) / 2
        
        print(f"Live Price (XAU/USD): {current_price}")

        for zone in TARGET_ZONES:
            target_val = zone['target']
            target_str = str(target_val)
            buffer = zone['pips'] * 0.01 # 10 pips = $0.10
            
            if (target_val - buffer) <= current_price <= (target_val + buffer):
                last_sent = state.get(target_str, 0)
                if time.time() - last_sent > COOLDOWN_SECONDS:
                    send_alert(current_price, target_val)
                    state[target_str] = time.time()
                else:
                    print(f"Price {current_price} is in zone {target_val}, but cooling down.")
        
        save_state(state)
    except Exception as e:
        print(f"Error parsing Swissquote data: {e}")

if __name__ == "__main__":
    check_price()
