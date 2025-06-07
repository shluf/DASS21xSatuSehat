from pymongo import MongoClient
from pymongo.server_api import ServerApi
from src.core.config import settings

uri_to_use = settings.MONGO_SRV_URI if "<db_password>" not in settings.MONGO_SRV_URI else settings.MONGO_DETAILS

if "<db_password>" in uri_to_use and uri_to_use == settings.MONGO_SRV_URI:
    print("WARNING: MongoDB password placeholder detected in MONGO_SRV_URI. Please replace <db_password>.")
    if settings.MONGO_DETAILS:
        print(f"Falling back to MONGO_DETAILS: {settings.MONGO_DETAILS}")
        uri_to_use = settings.MONGO_DETAILS
    else:
        raise ValueError("MONGO_SRV_URI requires a password, and no fallback MONGO_DETAILS is configured.")


client = MongoClient(uri_to_use, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

db = client[settings.DATABASE_NAME]

def get_database():
    return db

def get_user_collection():
    return db[settings.USER_COLLECTION] 