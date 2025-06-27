import requests
from notion_client import Client
import os

# ----------------------------
# ENVIRONMENT VARIABLES
# ----------------------------
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")  # store safely in Render
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"

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

    # 2. Loop through Notion database items
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]
        symbol = props["Symbol"]["rich_text"][0]["plain_text"].lower()
        
        # 3. Find matching coin in CoinGecko data
        matching = next((coin for coin in market_data if coin["symbol"] == symbol), None)
        if matching:
            current_price = matching["current_price"]
            # 4. Update Notion record
            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Current Price": {
                        "number": current_price
                    }
                }
            )
            print(f"Updated {symbol.upper()} to ${current_price}")
        else:
            print(f"{symbol.upper()} not found on CoinGecko")

if __name__ == "__main__":
    update_prices()
