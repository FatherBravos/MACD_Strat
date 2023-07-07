import requests
import pandas as pd
from pymongo import MongoClient
from dateutil import parser
import time

# Set the Binance API
binance_api_key = 'E7iabPzYjvhe5lQb1V5tFlqracfQ7QnjCOgOZLjnLIsKaFslDgHyssYr2Q9eGyau'
binance_api_secret = 'iC6k2QshTLGUFSF5XLYEtMngDGRC9cjpoYAtMJyz54DBhUfDPD5ScDUAHUPNlXND'
binance_endpoint = 'https://fapi.binance.com/fapi/v1/klines'

# User inputs
symbol = "SOLUSDT"
interval = "1m"   # 1m, 1h, 1d
startTime = "1577836800000"
endTime = "1685318400000"
ticker = "SOLUSDT"
granularity = "1min"
market_type = "usdm"
price_type = "last"
collection_name = "binance_SOLUSDT"

# Set the headers
headers = {
    'X-MBX-APIKEY': binance_api_key
}

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Assuming local MongoDB instance at default port 27017
db = client['market_data']  # Replace 'crypto_db' with your database name
collection = db[collection_name]

# Set the parameters
params = {
    'symbol': symbol,
    'interval': interval,
    'startTime': startTime,
    'endTime': endTime,
    'limit': 1500
}

# While loop to fetch data until the end time
while True:
    # Send GET request
    response = requests.get(binance_endpoint, headers=headers, params=params)
    # Check the response status
    if response.status_code == 200:
        data = response.json()

        if len(data) == 0:
            # If no more data is returned by the API
            break

        # Prepare the data
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                         'Close time', 'Quote asset volume', 'Number of trades',
                                         'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['ticker'] = ticker
        df['granularity'] = granularity
        df['market_type'] = market_type
        df['price_type'] = price_type

        # Insert data into MongoDB
        collection.insert_many(df.to_dict('records'))

        # Update start time to the next timestamp
        params['startTime'] = str(int(df['timestamp'].max().timestamp() * 1000 + 1))

        # Delay to avoid hitting the API rate limit
        time.sleep(1)

    else:
        print(f'Response Error: {response.status_code}')
        break

print(f'Data successfully inserted into collection: {collection_name}')
