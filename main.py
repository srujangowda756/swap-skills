from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal
from secret_store import load_secrets

from routes.user import user_router
from routes.skills import skill_router
from routes.user_skills import user_skill_router
from routes.swap_requests import swap_request_router
from routes.messages import message_router
from routes.conversations import conversation_router
from routes.notifications import notification_router
from routes.session import session_router
from routes.review import review_router
from routes.websocket import ws_router
from routes.admin import admin_router


# Load secrets when the application starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as db:
        await load_secrets(db)

    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(user_router)
app.include_router(skill_router)
app.include_router(user_skill_router)
app.include_router(swap_request_router)
app.include_router(message_router)
app.include_router(conversation_router)
app.include_router(notification_router)
app.include_router(session_router)
app.include_router(review_router)
app.include_router(ws_router)
app.include_router(admin_router)
