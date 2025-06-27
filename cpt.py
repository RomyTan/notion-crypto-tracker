import requests
from notion_client import Client
import os

# ----------------------------
# ENVIRONMENT VARIABLES
# ----------------------------
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
COINGECKO_API_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,usd-coin&vs_currencies=usd"
)

# ----------------------------
# SYMBOL to COIN ID MAP
# ----------------------------
COIN_ID_MAP = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "usdc": "usd-coin",
}

# ----------------------------
# INIT NOTION CLIENT
# ----------------------------
notion = Client(auth=NOTION_TOKEN)

# ----------------------------
# MAIN FUNCTION
# ----------------------------
def update_prices():
    response = requests.get(COINGECKO_API_URL)
    if response.status_code != 200:
        print("Failed to fetch CoinGecko data")
        return
    market_data = response.json()

    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]
        symbol = props["Symbol"]["rich_text"][0]["plain_text"].lower()
        coin_id = COIN_ID_MAP.get(symbol)
        if not coin_id:
            print(f"{symbol.upper()} not mapped in COIN_ID_MAP")
            continue

        current_price = market_data.get(coin_id, {}).get("usd")
        if current_price:
            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Current Price": {"number": current_price}
                }
            )
            print(f"Updated {symbol.upper()} to ${current_price}")
        else:
            print(f"{symbol.upper()} price not found from CoinGecko")

if __name__ == "__main__":
    update_prices()
