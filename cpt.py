import requests
from notion_client import Client
import os
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"

notion = Client(auth=NOTION_TOKEN)

def update_notion():
    # fetch market data
    response = requests.get(COINGECKO_API_URL)
    if response.status_code != 200:
        print("Failed to fetch CoinGecko data")
        return
    coins = response.json()

    # query notion database
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]
        symbol = props["Symbol"]["title"][0]["plain_text"].lower()
        purchase_date = props.get("Purchase Date", {}).get("date", {}).get("start")

        if not purchase_date:
            print(f"{symbol.upper()}: No purchase date found, skipping.")
            continue

        # format date for CoinGecko
        dt = datetime.fromisoformat(purchase_date)
        coingecko_date = dt.strftime("%d-%m-%Y")

        print(f"{symbol.upper()}: fetching historical price for {coingecko_date}")

        # find CoinGecko ID
        matching = next((c for c in coins if c["symbol"] == symbol), None)
        if matching:
            coin_id = matching["id"]
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={coingecko_date}"
            hist = requests.get(url)
            if hist.status_code != 200:
                print(f"{symbol.upper()}: CoinGecko returned {hist.status_code} on history request")
                continue

            hist_data = hist.json()
            price = hist_data.get("market_data", {}).get("current_price", {}).get("usd")
            if price:
                notion.pages.update(
                    page_id=page["id"],
                    properties={
                        "Purchase Price": {"number": price}
                    }
                )
                print(f"{symbol.upper()}: purchase price updated to {price}")
            else:
                print(f"{symbol.upper()}: no price found in historical data")
        else:
            print(f"{symbol.upper()}: no match found on CoinGecko")

if __name__ == "__main__":
    update_notion()
