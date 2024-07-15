import jwt
import os
import csv
from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse, FileResponse
from server.models.user import (UserSchema, LoginSchema, ResponseModel, ErrorResponseModel, Journey, GPSPingSchema, EndJourneySchema)
from server.database import user_collection, hash_password, verify_password, user_helper, journey_collection, add_journey
from datetime import datetime, timedelta
from bson import ObjectId
from mappymatch import package_root
from mappymatch.constructs.geofence import Geofence
from mappymatch.constructs.trace import Trace
from mappymatch.maps.nx.nx_map import NxMap
from mappymatch.matchers.lcss.lcss import LCSSMatcher
from mappymatch.utils.plot import plot_matches

router = APIRouter()

SECRET_KEY = "SECRET_KEY"

# helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=365)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# Authentication middleware to check token validity
auth_scheme = HTTPBearer()
async def get_current_user(Authtoken: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = Authtoken.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "role": role}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authorization middleware to check if user is admin
async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


# route handlers
@router.post("/register", response_description="User data added into the database")
async def register_user(user: UserSchema = Body(...)):
    try:
        existing_user = user_collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=409, detail="User with this email already exists")
        
        user = jsonable_encoder(user)
        user["password"] = hash_password(user["password"])
        user["createdAt"] = datetime.now()
        user["updatedAt"] = datetime.now()
        new_user = user_collection.insert_one(user)
        created_user = user_collection.find_one({"_id": new_user.inserted_id})
        return JSONResponse(status_code=201, content=ResponseModel(user_helper(created_user), "User registered successfully."))
    except Exception as e:
        if (type(e) == HTTPException):
            return ErrorResponseModel(e.detail, e.status_code, e.detail)
        return ErrorResponseModel(str(e), 500, "Internal Server Error")

@router.post("/login", response_description="User login")
async def login_user(user: LoginSchema = Body(...)):
    try:
        user_data = user_collection.find_one({"email": user.email})
        if user_data is None or not verify_password(user.password, user_data["password"]):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        access_token = create_access_token(data={"sub": str(user_data["_id"]), "role": user_data["role"]})
        refresh_token = create_refresh_token(data={"sub": str(user_data["_id"]), "role": user_data["role"]})

        return JSONResponse(status_code=200, content=ResponseModel({"user": user_helper(user_data), "access_token": access_token, "refresh_token": refresh_token}, "User logged in successfully."))
    except Exception as e:
        if (type(e) == HTTPException):
            return ErrorResponseModel(e.detail, e.status_code, e.detail)
        return ErrorResponseModel(str(e), 500, "Internal Server Error")

@router.get("/riders", response_description="List all riders")
async def get_riders(current_user: dict = Depends(get_admin_user)):
    try:
        riders = user_collection.find({"role": "rider"})
        return JSONResponse(status_code=200, content=ResponseModel([user_helper(rider) for rider in riders], "Riders fetched successfully."))
    except Exception as e:
        return ErrorResponseModel(str(e), 500, "Internal Server Error")

@router.post("/start_journey", response_description="Start rider journey")
async def start_journey(current_user: dict = Depends(get_current_user)):
    try:
        # Add a new journey record to the database
        journey_data = {"rider_id": current_user['user_id']}
        new_journey = add_journey(journey_data)

        # Create the necessary directories
        journey_id = new_journey["_id"]
        rider_folder = f"app/server/journeys/{current_user['user_id']}"
        input_folder = f"{rider_folder}/input_journeys"
        output_folder = f"{rider_folder}/output_journeys"
        os.makedirs(input_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        # Create a new CSV file for the journey
        csv_file = f"{input_folder}/{journey_id}_input.csv"
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['latitude', 'longitude'])

        return JSONResponse(status_code=200, content=ResponseModel({"journey_id": journey_id}, "Journey started successfully."))
    except Exception as e:
        return ErrorResponseModel(str(e), 500, "Internal Server Error")

@router.post("/gps_ping", response_description="Get the rider's GPS ping")
async def create_riders_gps_ping(GPSPing: GPSPingSchema = Body(...), current_user: dict = Depends(get_current_user)):
    try:
        rider_folder = f"app/server/journeys/{current_user['user_id']}"
        input_folder = f"{rider_folder}/input_journeys"

        csv_file = f"{input_folder}/{GPSPing.journey_id}_input.csv"
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([GPSPing.latitude, GPSPing.longitude])

        return JSONResponse(status_code=200, content=ResponseModel({"message": "Ping recorded successfully."}, "Ping recorded successfully."))
    except Exception as e:
        return ErrorResponseModel(str(e), 500, "Internal Server Error")

@router.post("/end_journey", response_description="End rider journey")
async def end_journey(end_journey: EndJourneySchema = Body(...), current_user: dict = Depends(get_current_user)):
    try:
        csv_file = f"./app/server/journeys/{current_user['user_id']}/input_journeys/{end_journey.journey_id}_input.csv"
        trace = Trace.from_csv(csv_file, lat_column="latitude", lon_column="longitude", xy=True)

        geofence = Geofence.from_trace(trace, padding=1e3)
        nx_map = NxMap.from_geofence(geofence)
        matcher = LCSSMatcher(nx_map)
        matches = matcher.match_trace(trace)

        output_map_path = f"./app/server/journeys/{current_user['user_id']}/output_journeys/{end_journey.journey_id}_output.html"
        output_csv_path = f"./app/server/journeys/{current_user['user_id']}/output_journeys/{end_journey.journey_id}_output.csv"

        map = plot_matches(matches.matches)
        map.save(output_map_path)

        df = matches.matches_to_dataframe()
        df.to_csv(output_csv_path, index=False)

        return JSONResponse(status_code=200, content=ResponseModel({"message": "Journey ended and processed successfully."}, "Journey ended and processed successfully."))
    
    except Exception as e:
        return ErrorResponseModel(str(e), 500, "Internal Server Error")
    
@router.get("/rider/{rider_id}/journeys", response_description="Get all journeys of a rider")
async def get_rider_journeys(rider_id: str, current_user: dict = Depends(get_admin_user)):
    try:
        rider = user_collection.find_one({"_id": ObjectId(rider_id)})
        if not rider:
            raise HTTPException(status_code=404, detail="Rider not found")

        journeys = journey_collection.find({"rider_id": rider_id}).sort("createdAt", 1)

        response = []
        for idx, journey in enumerate(journeys):
            response.append({
                "fullName": rider["fullname"],
                "riderId": rider_id,
                "journeyNo": idx + 1,
                "journeyId": str(journey["_id"])
            })

        return JSONResponse(status_code=200, content=ResponseModel(response, "Rider's journeys fetched successfully."))
    
    except Exception as e:
        return ErrorResponseModel(str(e), 500, "Internal Server Error")
    
@router.get("/rider/{rider_id}/journeys/{journey_id}/map", response_description="Get the journey map HTML")
async def get_journey_map(rider_id: str, journey_id: str, current_user: dict = Depends(get_admin_user)):
    try:
        output_map_path = f"./app/server/journeys/{rider_id}/output_journeys/{journey_id}_output.html"

        # Check if the file exists
        if not os.path.exists(output_map_path):
            raise HTTPException(status_code=404, detail="Map not found")

        # Return the HTML file
        return FileResponse(path=output_map_path, media_type="text/html", filename=f"{journey_id}_output.html")

    except Exception as e:
        if (type(e) == HTTPException):
            return ErrorResponseModel(e.detail, e.status_code, e.detail)
        return ErrorResponseModel(str(e), 500, "Internal Server Error")