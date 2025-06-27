import requests
from notion_client import Client
import os
from datetime import datetime

# ----------------------------
# ENVIRONMENT VARIABLES
# ----------------------------
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
COINGECKO_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/{id}/history?date={date}"

# ----------------------------
# INIT NOTION CLIENT
# ----------------------------
notion = Client(auth=NOTION_TOKEN)

# ----------------------------
# MAIN FUNCTION
# ----------------------------
def update_prices():
    # 1. Get market data
    response = requests.get(COINGECKO_API_URL)
    if response.status_code != 200:
        print("Failed to fetch CoinGecko data")
        return
    market_data = response.json()

    # 2. Query Notion database
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]
        # renamed Coin column
        symbol = props["Coin"]["title"][0]["plain_text"].lower()
        purchase_date = props["Purchase Date"].get("date", {}).get("start", None)

        # 3. Find matching coin
        matching = next((coin for coin in market_data if coin["symbol"] == symbol), None)
        if not matching:
            print(f"{symbol.upper()} not found on CoinGecko")
            continue

        current_price = matching["current_price"]

        # default purchase price
        purchase_price = None
        if purchase_date:
            dt = datetime.fromisoformat(purchase_date)
            date_str = dt.strftime("%d-%m-%Y")
            history_url = COINGECKO_HISTORY_URL.format(id=matching["id"], date=date_str)
            hist_response = requests.get(history_url)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                market_hist = hist_data.get("market_data", {}).get("current_price", {}).get("usd", None)
                if market_hist:
                    purchase_price = market_hist
                    print(f"{symbol.upper()}: purchase price updated to {purchase_price}")
                else:
                    print(f"{symbol.upper()}: no price data on that date")
            else:
                print(f"{symbol.upper()}: failed to fetch historical price")
        else:
            print(f"{symbol.upper()}: no purchase date set")

        # 4. Compose update properties
        update_props = {
            "Current Price": {"number": current_price}
        }
        if purchase_price:
            update_props["Purchase Price"] = {"number": purchase_price}

        # 5. Update Notion page
        notion.pages.update(
            page_id=page["id"],
            properties=update_props,
            icon={
                "type": "external",
                "external": {
                    "url": matching["image"]
                }
            }
        )
        print(f"{symbol.upper()}: updated current price to ${current_price} and icon updated")

if __name__ == "__main__":
    update_prices()
