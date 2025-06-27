import requests
from notion_client import Client
import os
from datetime import datetime

# ----------------------------
# ENVIRONMENT VARIABLES
# ----------------------------
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# ----------------------------
# INIT NOTION CLIENT
# ----------------------------
notion = Client(auth=NOTION_TOKEN)

# ----------------------------
# MAIN FUNCTION
# ----------------------------
def update_notion():
    # 1. get live market data
    live_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
    live_response = requests.get(live_url)
    if live_response.status_code != 200:
        print("Failed to fetch CoinGecko market data")
        return
    market_data = live_response.json()

    # 2. query notion database
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]

        # get symbol from title
        try:
            symbol = props["Symbol"]["title"][0]["plain_text"].lower()
        except (KeyError, IndexError):
            print("Missing or invalid symbol in page")
            continue

        # get purchase date
        purchase_date_str = props.get("Purchase Date", {}).get("date", {}).get("start")
        if not purchase_date_str:
            print(f"{symbol.upper()} has no purchase date, skipping purchase price update")
            continue

        purchase_date = datetime.fromisoformat(purchase_date_str)
        unix_timestamp = int(purchase_date.timestamp())

        # fetch historical price
        hist_url = f"https://api.coingecko.com/api/v3/coins/{symbol}/history?date={purchase_date.strftime('%d-%m-%Y')}"
        hist_response = requests.get(hist_url)
        if hist_response.status_code != 200:
            print(f"Failed to fetch historical price for {symbol.upper()}")
            continue

        hist_data = hist_response.json()
        try:
            purchase_price = hist_data["market_data"]["current_price"]["usd"]
        except (KeyError, TypeError):
            print(f"No historical price found for {symbol.upper()}")
            continue

        # get current price from live
        matching = next((c for c in market_data if c["symbol"] == symbol), None)
        if not matching:
            print(f"{symbol.upper()} not found in live data")
            continue
        current_price = matching["current_price"]

        # update Notion
        notion.pages.update(
            page_id=page["id"],
            properties={
                "Current Price": {"number": current_price},
                "Purchase Price": {"number": purchase_price},
            }
        )
        print(f"{symbol.upper()}: purchase price ${purchase_price}, current price ${current_price} updated.")

if __name__ == "__main__":
    update_notion()
