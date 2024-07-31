from fastapi import FastAPI
from server.routes.auth import router as AuthRouter
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
origins = [
    "http://localhost:3000",  # React frontend origin
    # Add other origins if necessary
]
# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(AuthRouter, tags=["User"], prefix="")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the logisync app!"}
