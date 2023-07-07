import csv
import pymongo
import datetime
import os

# MongoDB connection information
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["market_data"]
collection = db["darwinex_GBPJPY"]

# Define metadata
metadata = {
    "ticker": "GBPJPY",
    "market_type": "spot",
    "price_type": "bid",
    "granularity": "1day"
}

# Define path to the file
path_to_file = r'C:\Users\49176\Desktop\Darwinex Data\GBPJPY_BID_1D.csv'

# Ensure the file exists before opening it
if os.path.isfile(path_to_file):
    # Read CSV and insert documents
    with open(path_to_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert UNIX epoch timestamp in milliseconds to datetime
            row["timestamp"] = datetime.datetime.fromtimestamp(int(row["timestamp"]) / 1000.0)
            row.update(metadata)
            row["open"] = float(row["open"])
            row["high"] = float(row["high"])
            row["low"] = float(row["low"])
            row["close"] = float(row["close"])
            row["volume"] = float(row["volume"])
            collection.insert_one(row)
else:
    print(f"The file {path_to_file} does not exist.")

# Print number of documents inserted
print(f"Inserted {collection.count_documents({'ticker': 'GBPJPY'})} documents into {collection.name} collection.")
