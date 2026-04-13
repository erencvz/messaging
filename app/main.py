import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Messaging API",
    version=os.getenv("APP_VERSION", "0.0.0"),
)

# --- Models ---

class MessageIn(BaseModel):
    id: str
    nickname: str
    message: str

class MessageOut(MessageIn):
    pass

class InfoOut(BaseModel):
    version: str
    environment: str
    build_sha: str

# --- In-memory store ---

messages: List[MessageOut] = []

# --- Endpoints ---

@app.post("/messages", response_model=MessageOut, status_code=201)
def create_message(body: MessageIn):
    msg = MessageOut(**body.model_dump())
    messages.append(msg)
    return msg

@app.get("/messages", response_model=List[MessageOut])
def list_messages():
    return messages

@app.get("/info", response_model=InfoOut)
def info():
    return InfoOut(
        version=os.getenv("APP_VERSION", "unknown"),
        environment=os.getenv("ENVIRONMENT", "unknown"),
        build_sha=os.getenv("BUILD_SHA", "unknown"),
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test1")
def health():
    return {"status": "test1"}

@app.get("/test2")
def health():
    return {"status": "test2"}
