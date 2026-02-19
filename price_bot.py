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

# Target Prices & Pip Zones (1 pip = 0.01)
TARGET_ZONES = [
    {"target": 2650.50, "pips": 2},
    {"target": 2610.00, "pips": 5}
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
    msg = MIMEText(f"Gold Alert! Price: {price} is near {target}.")
    msg['Subject'] = f"GOLD ALERT: {price}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    except Exception as e:
        print(f"Email error: {e}")

def check_price():
    state = load_state()
    try:
        response = requests.get(URL, timeout=15)
        data = response.json()
        
        # DEBUG: Let's see what we actually got
        print(f"Raw API Data: {data}")

        # Swissquote returns a list. Let's find the first item safely.
        if isinstance(data, list) and len(data) > 0:
            item = data[0]
            # Try to find bid/ask using multiple possible keys
            bid = item.get('bidPrice') or item.get('bid')
            ask = item.get('askPrice') or item.get('ask')
            
            if bid and ask:
                current_price = (float(bid) + float(ask)) / 2
                print(f"Successfully calculated price: {current_price}")
                
                for zone in TARGET_ZONES:
                    target_val = zone['target']
                    target_str = str(target_val)
                    buffer = zone['pips'] * 0.01
                    
                    if (target_val - buffer) <= current_price <= (target_val + buffer):
                        last_sent = state.get(target_str, 0)
                        if time.time() - last_sent > COOLDOWN_SECONDS:
                            send_alert(current_price, target_val)
                            state[target_str] = time.time()
                            print(f"Alert TRIGGERED for {target_val}")
                        else:
                            print(f"Price in zone for {target_val}, but on cooldown.")
                save_state(state)
            else:
                print("Error: 'bidPrice' or 'askPrice' keys missing from the item.")
        else:
            print("Error: API returned an empty list or unexpected format.")

    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    check_price()
