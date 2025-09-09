from fastapi import FastAPI
from database import Base, engine

# Router
from urls.routes import router as pings_router

# Models
from urls import models

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(pings_router,prefix="/api/v1/url", tags=["Urls"])