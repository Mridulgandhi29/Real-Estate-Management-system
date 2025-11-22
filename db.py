import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Default: local MongoDB; or put your Atlas URI in a .env file as MONGO_URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["real_estate_db"]

properties_col = db["properties"]
owners_col = db["owners"]
transactions_col = db["transactions"]
