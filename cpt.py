import requests
from notion_client import Client
import os

# Environment variables
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"

# Initialize Notion client
notion = Client(auth=NOTION_TOKEN)

def update_notion():
    # Fetch data from CoinGecko
    response = requests.get(COINGECKO_API_URL)
    if response.status_code != 200:
        print("Failed to fetch CoinGecko data")
        return

    coins = response.json()

    # Query Notion database
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    for page in query["results"]:
        props = page["properties"]
        print("DEBUG props:", props)  # print all props for troubleshooting

        try:
            symbol = props["Symbol"]["title"][0]["plain_text"].lower()
        except (KeyError, IndexError):
            print("Skipping page due to missing Symbol property.")
            continue

        # Match with CoinGecko
        matching = next((c for c in coins if c["symbol"] == symbol), None)
        if matching:
            current_price = matching["current_price"]

            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Current Price": {"number": current_price}
                }
            )
            print(f"{symbol.upper()}: updated current price to ${current_price}")
        else:
            print(f"{symbol.upper()} not found on CoinGecko")

if __name__ == "__main__":
    update_notion()
