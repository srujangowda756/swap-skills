from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user import user_router
from routes.skills import skill_router
from routes.user_skills import user_skill_router
from routes.swap_requests import swap_request_router
from routes.messages import message_router
from routes.conversations import conversation_router


app = FastAPI()

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
