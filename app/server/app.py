from fastapi import FastAPI
from server.routes.auth import router as AuthRouter
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this based on your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(AuthRouter, tags=["User"], prefix="")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the logisync app!"}
