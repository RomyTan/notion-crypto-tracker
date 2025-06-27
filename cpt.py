import requests
from notion_client import Client
import os
from datetime import datetime

# ENVIRONMENT
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

def update_notion():
    # 1. get current market data
    live_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250"
    live_response = requests.get(live_url)
    if live_response.status_code != 200:
        print("Failed to fetch CoinGecko market data")
        return
    market_data = live_response.json()

    # 2. query notion database
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]

        # get coin from select
        try:
            symbol = props["Coin"]["select"]["name"].lower()
        except (KeyError, TypeError):
            print("No Coin selected on this row, skipping.")
            continue

        # get purchase date
        purchase_date_str = props.get("Purchase Date", {}).get("date", {}).get("start")
        if not purchase_date_str:
            print(f"{symbol.upper()}: No purchase date found, skipping purchase price update")
            continue

        purchase_date = datetime.fromisoformat(purchase_date_str)
        coingecko_date = purchase_date.strftime("%d-%m-%Y")

        # find CoinGecko ID from live market data
        matching = next((c for c in market_data if c["symbol"] == symbol), None)
        if not matching:
            print(f"{symbol.upper()}: not found on CoinGecko")
            continue
        coin_id = matching["id"]

        # 3. get historical price
        hist_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={coingecko_date}"
        hist_response = requests.get(hist_url)
        if hist_response.status_code != 200:
            print(f"{symbol.upper()}: failed to fetch history from CoinGecko")
            continue

        hist_data = hist_response.json()
        purchase_price = hist_data.get("market_data", {}).get("current_price", {}).get("usd")
        if purchase_price is None:
            print(f"{symbol.upper()}: no historical price data found")
            continue

        current_price = matching["current_price"]

        # update Notion
        notion.pages.update(
            page_id=page["id"],
            properties={
                "Purchase Price": {"number": purchase_price},
                "Current Price": {"number": current_price}
            }
        )

        print(f"{symbol.upper()}: updated purchase price to ${purchase_price}, current price to ${current_price}")

if __name__ == "__main__":
    update_notion()
