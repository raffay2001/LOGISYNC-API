from fastapi import FastAPI
from server.routes.auth import router as AuthRouter


app = FastAPI()

app.include_router(AuthRouter, tags=["User"], prefix="")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the logisync app!"}
