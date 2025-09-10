from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from users.models import User
from users.schemas import UserCreate, UserRead, UserUpdate
from users.users import auth_backend, current_active_user, fastapi_users
from database import create_db_and_tables

# Router
from urls.routes import router as pings_router
from url_scheduler.routes import router as schedule_router
from reporting.routes import router as oyen_ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Oyen API", description="Oyen API for devops")

app.include_router(pings_router,prefix="/api/v1/url", tags=["Urls"])
app.include_router(schedule_router,prefix="/api/v1/url-schedule", tags=["Urls Scheduler"])
app.include_router(oyen_ai_router, prefix="/api/v1/reporting", tags=["Reporting"])

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/users",
    tags=["users"],
)

@app.get("/api/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}