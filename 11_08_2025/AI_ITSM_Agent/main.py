# backend/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_itsm_agent, session_store
from llm_interface import classify_issue_intent, ask_llm

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


class MessageInput(BaseModel):
    message: str

@app.post("/classify_intent")
def classify_intent(input: MessageInput):
    message = input.message
    agent_type = classify_issue_intent(message)  # e.g., returns 'itsm', 'location', etc.
    return {"agent_type": agent_type}

class AgentTypeRequest(BaseModel):
    agent_type: str

@app.post("/generate_intro")
async def generate_intro(req: AgentTypeRequest):
    agent_name = req.agent_type.replace("_", " ").title()
    prompt = f"""
You are acting as the "{agent_name}" helpful support assistant.

Introduce yourself clearly by saying something like "Hi, I'm your {agent_name} Agent" or similar. Be friendly and speak in helpful tone.

Then politely ask the user to describe their issue. Do NOT ask for IDs, codes, or technical details — just prompt them to explain the issue.

Respond in a single, human-friendly sentence or two.
"""
    response = ask_llm(prompt)
    return {"intro_message": response.strip()}    