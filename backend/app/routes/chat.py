from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv

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

DEFAULT_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"]
SYSTEM_INSTRUCTION = (
    "You are ASHURA, a helpful and powerful AI assistant. "
    "Respond clearly and concisely. Use markdown formatting when appropriate — "
    "use headings, bold, code blocks, and lists to make your answers easy to read. "
    "When writing code, always specify the programming language in fenced code blocks."
)

_client = None


def _build_prompt(system: str, history, user_message: str) -> str:
    prompt_lines = [system]
    for msg in history:
        if msg.role == "user":
            prompt_lines.append(f"User: {msg.content}")
        else:
            prompt_lines.append(f"Assistant: {msg.content}")
    prompt_lines.append(f"User: {user_message}")
    prompt_lines.append("Assistant:")
    return "\n".join(prompt_lines)


def _query_models(prompt: str) -> str:
    client = get_client()
    last_error = None
    for model in DEFAULT_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=512,
                ),
            )
            return response.text
        except Exception as e:
            err = str(e).lower()
            if "quota exceeded" in err or "rate limit" in err:
                last_error = e
                continue
            raise
    if last_error is not None:
        raise HTTPException(
            status_code=429,
            detail=(
                "Gemini quota exceeded across default models. "
                "Enable billing or use another API key."
            ),
        )
    raise HTTPException(
        status_code=500,
        detail="Failed to generate response from Gemini models.",
    )


def get_client():
    """Return a cached Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail=(
                    "GEMINI_API_KEY is not set. "
                    "Add it to your backend/.env file."
                ),
            )
        print(f"[INFO] Initializing Gemini client with key: {api_key[:8]}...")
        _client = genai.Client(api_key=api_key)
    return _client


def _build_messages(system: str, history, user_message: str) -> list:
    """Build Gemini chat message array with system + history + newest user message."""
    messages = [{"role": "system", "content": system}]
    for msg in history:
        role = "user" if msg.role == "user" else "assistant"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _generate_title(user_message: str) -> str:
    """Use Gemini to generate a short conversation title."""
    try:
        prompt = (
            f"Generate a very short concise title (max 5 words, no quotes, "
            f"no punctuation at end) for a conversation that starts with: \"{user_message}\""
        )
        return _query_models(prompt).split('\n')[0][:50]
    except Exception:
        return user_message[:40] + "..." if len(user_message) > 40 else user_message


# ── Conversations ─────────────────────────────────────────────────────────────


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(db: Session = Depends(get_db)):
    convo = Conversation()
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
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
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo.title = body.title
    db.commit()
    db.refresh(convo)
    return convo


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(convo)
    db.commit()
    return {"detail": "Conversation deleted"}


# ── Chat ──────────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get a full response."""
    if request.conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = Conversation()
        db.add(convo)
        db.commit()
        db.refresh(convo)

    history = convo.messages
    user_msg = Message(conversation_id=convo.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    try:
        prompt = _build_prompt(SYSTEM_INSTRUCTION, history, request.message)
        assistant_text = _query_models(prompt)


        assistant_msg = Message(
            conversation_id=convo.id,
            role="assistant",
            content=assistant_text,
        )
        db.add(assistant_msg)

        if convo.title == "New Chat":
            convo.title = _generate_title(request.message)

        db.commit()

        return ChatResponse(response=assistant_text, conversation_id=convo.id)

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "api_key" in error_str.lower() or "authentication" in error_str.lower():
            detail = (
                "GEMINI_API_KEY is invalid or account has no quota. "
                "Check your API key in backend/.env."
            )
        else:
            detail = f"Error: {error_str}"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and stream the response via Server-Sent Events."""
    if request.conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = Conversation()
        db.add(convo)
        db.commit()
        db.refresh(convo)

    history = convo.messages
    user_msg = Message(conversation_id=convo.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    conversation_id = convo.id
    is_new_chat = convo.title == "New Chat"
    user_message_text = request.message
    messages = _build_messages(SYSTEM_INSTRUCTION, history, request.message)

    def event_generator():
        try:
            client = get_client()
        except HTTPException as e:
            yield f"data: {json.dumps({'type': 'error', 'content': e.detail})}\n\n"
            return

        full_response = ""
        db_inner = next(get_db())

        try:
            full_response = ""
            prompt = _build_prompt(SYSTEM_INSTRUCTION, history, user_message_text)

            for model in DEFAULT_MODELS:
                try:
                    stream = client.models.generate_content_stream(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=512,
                        ),
                    )
                    for chunk in stream:
                        text_chunk = getattr(chunk, "text", "")
                        if text_chunk:
                            full_response += text_chunk
                            data = json.dumps({
                                "type": "chunk",
                                "content": text_chunk,
                                "conversation_id": conversation_id,
                            })
                            yield f"data: {data}\n\n"

                    assistant_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_response,
                    )
                    db_inner.add(assistant_msg)
                    break

                except Exception as e:
                    err_lower = str(e).lower()
                    if "quota exceeded" in err_lower or "rate limit" in err_lower:
                        continue
                    raise

            else:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Gemini streaming quota exceeded for all fallback models. "
                        "Enable billing or change API key."
                    ),
                )

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

            data = json.dumps({"type": "done", "conversation_id": conversation_id})
            yield f"data: {data}\n\n"

        except Exception as e:
            error_str = str(e)
            if "403" in error_str or "api_key" in error_str.lower() or "authentication" in error_str.lower():
                error_content = "GEMINI_API_KEY is invalid or account has no quota. Check your API key in backend/.env."
            else:
                error_content = error_str
            data = json.dumps({"type": "error", "content": error_content})
            yield f"data: {data}\n\n"
        finally:
            db_inner.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")