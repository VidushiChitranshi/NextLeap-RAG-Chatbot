import os
import logging
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the chatbot builder from main.py
from main import build_chatbot

# ── Load Environment ──────────────────────────────────────────────────────
load_dotenv()

# ── Setup FastAPI ──────────────────────────────────────────────────────────
app = FastAPI(title="NextLeap RAG Chatbot")

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

if not os.path.exists(static_dir):
    os.makedirs(static_dir)
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# ── Initialize Chatbot ────────────────────────────────────────────────────
# Note: This runs on startup. In production, consider lazy loading or 
# using a lifecycle event.
try:
    chatbot_instance = build_chatbot()
except Exception as e:
    print(f"CRITICAL: Failed to initialize chatbot: {e}")
    chatbot_instance = None

# ── Data Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

class Citation(BaseModel):
    label: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[str]
    is_fallback: bool
    success: bool
    error: Optional[str] = None

# ── Routes ────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        reply = chatbot_instance.chat(request.message)
        return ChatResponse(
            answer=reply.answer,
            citations=reply.citations,
            is_fallback=reply.is_fallback,
            success=reply.success,
            error=reply.error
        )
    except Exception as e:
        return ChatResponse(
            answer="",
            citations=[],
            is_fallback=False,
            success=False,
            error=str(e)
        )

@app.post("/clear")
async def clear_history():
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    chatbot_instance.clear_history()
    return {"status": "success", "message": "History cleared"}

# ── Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
