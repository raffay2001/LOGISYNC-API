# database.py

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from passlib.context import CryptContext

# Database connection
MONGO_DB_URI = "mongodb+srv://raffay2001:1234@oi-ecommerce.w8liexg.mongodb.net/?retryWrites=true&w=majority&appName=OI-ECOMMERCE"
client = MongoClient(MONGO_DB_URI)
database = client["logisync"]
user_collection = database["users"]
journey_collection = database["journeys"]

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def user_helper(user) -> dict:
    return {
        "_id": str(user["_id"]),
        "fullname": user["fullname"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "createdAt": str(user["createdAt"]),
        "updatedAt": str(user["updatedAt"]),
    }

def journey_helper(journey) -> dict:
    return {
        "_id": str(journey["_id"]),
        "rider_id": journey["rider_id"],
        "createdAt": str(journey["createdAt"]),
        "updatedAt": str(journey["updatedAt"]),
    }

# Retrieve user
def retrieve_user(email: str):
    return user_collection.find_one({"email": email})

# Add a new user
def add_user(user_data: dict) -> dict:
    user_data["password"] = hash_password(user_data["password"])
    user_data["createdAt"] = datetime.now()
    user_data["updatedAt"] = datetime.now()
    user = user_collection.insert_one(user_data)
    new_user = user_collection.find_one({"_id": user.inserted_id})
    return user_helper(new_user)

# Add a new journey
def add_journey(journey_data: dict) -> dict:
    journey_data["createdAt"] = datetime.now()
    journey_data["updatedAt"] = datetime.now()
    journey = journey_collection.insert_one(journey_data)
    new_journey = journey_collection.find_one({"_id": journey.inserted_id})
    return journey_helper(new_journey)
