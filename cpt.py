import requests
from notion_client import Client
import os

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

def update_notion():
    # fetch CoinGecko market data
    coins = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd").json()

    # get database pages
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)

    for page in query["results"]:
        props = page["properties"]

        # read symbol from title
        symbol = props["Symbol"]["title"][0]["plain_text"].lower()

        # find coin in CoinGecko
        matching = next((c for c in coins if c["symbol"] == symbol), None)
        if not matching:
            print(f"{symbol.upper()}: coin not found on CoinGecko")
            continue

        # current price
        current_price = matching["current_price"]

        # get purchase date
        purchase_date = props.get("Purchase Date", {}).get("date", {}).get("start", None)
        purchase_price = None

        if purchase_date:
            # fetch historical price
            cg_id = matching["id"]
            date_fmt = purchase_date.split("T")[0].split("-")
            date_str = f"{date_fmt[2]}-{date_fmt[1]}-{date_fmt[0]}"
            history_url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/history?date={date_str}"
            hist = requests.get(history_url).json()
            try:
                purchase_price = hist["market_data"]["current_price"]["usd"]
            except:
                print(f"{symbol.upper()}: failed to get historical price for {purchase_date}")

        # update Notion
        update_props = {
            "Current Price": {"number": current_price}
        }
        if purchase_price:
            update_props["Purchase Price"] = {"number": purchase_price}

        notion.pages.update(
            page_id=page["id"],
            properties=update_props
        )
        print(f"{symbol.upper()}: updated current price to {current_price} and purchase price to {purchase_price}")

if __name__ == "__main__":
    update_notion()
