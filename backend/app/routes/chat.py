from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from google import genai
import os
import json
from dotenv import load_dotenv

# Load .env explicitly using absolute path — works regardless of cwd or import order
_env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
)
load_dotenv(_env_path, override=True)

from ..database import get_db
from ..models import Conversation, Message
from ..schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationRenameRequest,
)

router = APIRouter(prefix="/api", tags=["chat"])

MODEL_NAME = "gemini-2.0-flash"  # fast, free quota, fully supported
SYSTEM_INSTRUCTION = (
    "You are a helpful, friendly AI assistant. "
    "Respond clearly and concisely. Use markdown formatting when appropriate — "
    "use headings, bold, code blocks, and lists to make your answers easy to read. "
    "When writing code, always specify the programming language in fenced code blocks."
)

# Lazy client cache — initialized on first request so dotenv is always loaded first
_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Return a cached Gemini client, initializing it on first call."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not set. Add it to your backend/.env file.",
            )
        print(f"[INFO] Initializing Gemini client with key: {api_key[:8]}...")
        _client = genai.Client(api_key=api_key)
    return _client


def _build_history(messages) -> list:
    """Convert DB messages to Gemini-compatible message history."""
    history = []
    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        history.append({"role": role, "parts": [{"text": msg.content}]})
    return history


def _generate_title(user_message: str) -> str:
    """Use Gemini to generate a short conversation title."""
    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=(
                f"Generate a very short concise title (max 5 words, no quotes, no punctuation at end) "
                f'for a conversation that starts with this message: "{user_message}"'
            ),
        )
        return response.text.strip().strip('"').strip("'")[:50]
    except Exception:
        return user_message[:40] + "..." if len(user_message) > 40 else user_message


# ── Conversations ─────────────────────────────────────────────────────────────


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    """List all conversations, newest first."""
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(db: Session = Depends(get_db)):
    """Create a new empty conversation."""
    convo = Conversation()
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get a conversation with all its messages."""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
def rename_conversation(
    conversation_id: str,
    body: ConversationRenameRequest,
    db: Session = Depends(get_db),
):
    """Rename a conversation."""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo.title = body.title
    db.commit()
    db.refresh(convo)
    return convo


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(convo)
    db.commit()
    return {"detail": "Conversation deleted"}


# ── Chat ──────────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get a full (non-streaming) response."""
    # Get or create conversation
    if request.conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = Conversation()
        db.add(convo)
        db.commit()
        db.refresh(convo)

    # Build history before saving the new user message
    history = _build_history(convo.messages)

    # Save user message
    user_msg = Message(conversation_id=convo.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    try:
        client = get_client()

        chat_session = client.chats.create(
            model=MODEL_NAME,
            history=history,
            config={"system_instruction": SYSTEM_INSTRUCTION},
        )
        response = chat_session.send_message(request.message)
        assistant_text = response.text

        # Save assistant message
        assistant_msg = Message(
            conversation_id=convo.id, role="assistant", content=assistant_text
        )
        db.add(assistant_msg)

        # Auto-generate title on first message
        if convo.title == "New Chat":
            convo.title = _generate_title(request.message)

        db.commit()

        return ChatResponse(response=assistant_text, conversation_id=convo.id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and stream the response via Server-Sent Events."""
    # Get or create conversation
    if request.conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = Conversation()
        db.add(convo)
        db.commit()
        db.refresh(convo)

    # Build history before saving the new user message
    history = _build_history(convo.messages)

    # Save user message
    user_msg = Message(conversation_id=convo.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    conversation_id = convo.id
    is_new_chat = convo.title == "New Chat"
    user_message_text = request.message

    def event_generator():
        # Validate client is available before streaming starts
        try:
            client = get_client()
        except HTTPException as e:
            yield f"data: {json.dumps({'type': 'error', 'content': e.detail})}\n\n"
            return

        full_response = ""
        db_inner = next(get_db())

        try:
            chat_session = client.chats.create(
                model=MODEL_NAME,
                history=history,
                config={"system_instruction": SYSTEM_INSTRUCTION},
            )

            for chunk in chat_session.send_message_stream(user_message_text):
                if chunk.text:
                    full_response += chunk.text
                    data = json.dumps({
                        "type": "chunk",
                        "content": chunk.text,
                        "conversation_id": conversation_id,
                    })
                    yield f"data: {data}\n\n"

            # Save full assistant response to DB
            assistant_msg = Message(
                conversation_id=conversation_id, role="assistant", content=full_response
            )
            db_inner.add(assistant_msg)

            # Auto-title on first message
            if is_new_chat:
                title = _generate_title(user_message_text)
                convo_obj = (
                    db_inner.query(Conversation)
                    .filter(Conversation.id == conversation_id)
                    .first()
                )
                if convo_obj:
                    convo_obj.title = title
                    data = json.dumps({
                        "type": "title",
                        "title": title,
                        "conversation_id": conversation_id,
                    })
                    yield f"data: {data}\n\n"

            db_inner.commit()

            # Signal completion
            data = json.dumps({"type": "done", "conversation_id": conversation_id})
            yield f"data: {data}\n\n"

        except Exception as e:
            data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {data}\n\n"
        finally:
            db_inner.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")