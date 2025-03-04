from fastapi import FastAPI
from app_mvp_vote import router as mvp_router

app = FastAPI()

app.include_router(mvp_router, prefix="/api", tags=["MVP Voting"])
