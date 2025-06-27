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
        symbol = props["Symbol"]["rich_text"][0]["plain_text"].lower()
        
        # find matching coin
        matching = next((c for c in coins if c["symbol"] == symbol), None)
        if matching:
            current_price = matching["current_price"]
            name = matching["name"]
            notion.pages.update(
                page_id=page["id"],
                properties={
                    "Current Price": {"number": current_price},
                    "Cryptocurrency": {"rich_text": [{"text": {"content": name}}]},
                }
            )
            print(f"{symbol.upper()}: updated current price to ${current_price} and name to {name}")
        else:
            print(f"{symbol.upper()} not found on CoinGecko")
