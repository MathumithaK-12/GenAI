# backend/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_itsm_agent, session_store

app = FastAPI()

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.post("/chat")
async def chat_endpoint(chat: ChatRequest):
    reply = run_itsm_agent(chat.message, chat.session_id)
    return {"response": reply}

@app.post("/end_chat")
async def end_chat(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    if session_id and session_id in session_store:
        del session_store[session_id]
    return {"status": "chat ended"}
