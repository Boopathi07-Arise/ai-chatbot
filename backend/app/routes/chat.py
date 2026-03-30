from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import os
import json
from dotenv import load_dotenv

# AI Model imports
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

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

_gemini_client = None
_openai_client = None
_claude_client = None


# ── Client Initialization ────────────────────────────────────────────────────


def _get_gemini_client():
    """Return a cached Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not set. Add it to your backend/.env file.",
            )
        if not GEMINI_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="google.generativeai is not installed.",
            )
        print(f"[INFO] Initializing Gemini client...")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def _get_openai_client():
    """Return a cached OpenAI client."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY is not set. Add it to your backend/.env file.",
            )
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="openai is not installed.",
            )
        print(f"[INFO] Initializing OpenAI client...")
        _openai_client = openai.OpenAI(api_key=api_key)
    return _openai_client


def _get_claude_client():
    """Return a cached Claude client."""
    global _claude_client
    if _claude_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY is not set. Add it to your backend/.env file.",
            )
        if not CLAUDE_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="anthropic is not installed.",
            )
        print(f"[INFO] Initializing Claude client...")
        _claude_client = anthropic.Anthropic(api_key=api_key)
    return _claude_client


# ── Model Integration Functions ───────────────────────────────────────────────


def call_gemini(message: str) -> str:
    """Call Gemini model and return response."""
    print("[INFO] Using Gemini model")
    client = _get_gemini_client()
    last_error = None
    
    for model in DEFAULT_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=message,
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
            detail="Gemini quota exceeded. Enable billing or use another API key.",
        )
    raise HTTPException(status_code=500, detail="Failed to generate response from Gemini.")


def call_gpt(message: str) -> str:
    """Call OpenAI GPT model and return response."""
    print("[INFO] Using OpenAI GPT model")
    client = _get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e).lower()
        if "insufficient_quota" in error_msg or "rate_limit" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="OpenAI quota exceeded or rate limited.",
            )
        if "api_key" in error_msg or "authentication" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="OpenAI API key is invalid.",
            )
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")


def call_claude(message: str) -> str:
    """Call Anthropic Claude model and return response."""
    print("[INFO] Using Anthropic Claude model")
    client = _get_claude_client()
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=512,
            system=SYSTEM_INSTRUCTION,
            messages=[
                {"role": "user", "content": message},
            ],
        )
        return response.content[0].text
    except Exception as e:
        error_msg = str(e).lower()
        if "rate_limit" in error_msg or "overloaded" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Claude rate limited or overloaded.",
            )
        if "api_key" in error_msg or "authentication" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Claude API key is invalid.",
            )
        raise HTTPException(status_code=500, detail=f"Claude error: {str(e)}")


def generate_response(model: str, message: str) -> str:
    """Route to the correct model based on selection."""
    model_lower = model.lower().strip()
    
    if model_lower == "gemini":
        return call_gemini(message)
    elif model_lower == "gpt":
        return call_gpt(message)
    elif model_lower == "claude":
        return call_claude(message)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model: {model}. Supported: 'gemini', 'gpt', 'claude'.",
        )


# ── Prompt Building ───────────────────────────────────────────────────────────


def _build_prompt(system: str, history, user_message: str) -> str:
    """Build text prompt from system, history, and user message."""
    prompt_lines = [system]
    for msg in history:
        if msg.role == "user":
            prompt_lines.append(f"User: {msg.content}")
        else:
            prompt_lines.append(f"Assistant: {msg.content}")
    prompt_lines.append(f"User: {user_message}")
    prompt_lines.append("Assistant:")
    return "\n".join(prompt_lines)




def _generate_title(user_message: str, model: str = "gemini") -> str:
    """Use AI model to generate a short conversation title."""
    try:
        prompt = (
            f"Generate a very short concise title (max 5 words, no quotes, "
            f"no punctuation at end) for a conversation that starts with: \"{user_message}\""
        )
        return generate_response(model, prompt).split('\n')[0][:50]
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
        assistant_text = generate_response(request.model, prompt)

        assistant_msg = Message(
            conversation_id=convo.id,
            role="assistant",
            content=assistant_text,
        )
        db.add(assistant_msg)

        if convo.title == "New Chat":
            convo.title = _generate_title(request.message, request.model)

        db.commit()

        return ChatResponse(response=assistant_text, conversation_id=convo.id)

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        raise HTTPException(status_code=500, detail=f"Error: {error_str}")


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
    model_name = request.model

    def event_generator():
        db_inner = next(get_db())
        full_response = ""

        try:
            prompt = _build_prompt(SYSTEM_INSTRUCTION, history, user_message_text)
            
            # For Gemini, use native streaming; for others, get full response and stream as single chunk
            if model_name.lower() == "gemini":
                # Gemini streaming implementation
                client = _get_gemini_client()
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
                        break
                    except Exception as e:
                        err_lower = str(e).lower()
                        if "quota exceeded" in err_lower or "rate limit" in err_lower:
                            continue
                        raise
                else:
                    raise HTTPException(
                        status_code=429,
                        detail="Gemini streaming quota exceeded. Enable billing or change API key.",
                    )
            else:
                # For OpenAI and Claude, get full response and stream as single chunk
                full_response = generate_response(model_name, prompt)
                data = json.dumps({
                    "type": "chunk",
                    "content": full_response,
                    "conversation_id": conversation_id,
                })
                yield f"data: {data}\n\n"

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
            )
            db_inner.add(assistant_msg)

            if is_new_chat:
                title = _generate_title(user_message_text, model_name)
                convo_obj = db_inner.query(Conversation).filter(Conversation.id == conversation_id).first()
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

        except HTTPException as e:
            data = json.dumps({"type": "error", "content": str(e.detail)})
            yield f"data: {data}\n\n"
        except Exception as e:
            error_str = str(e)
            data = json.dumps({"type": "error", "content": error_str})
            yield f"data: {data}\n\n"
        finally:
            db_inner.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")