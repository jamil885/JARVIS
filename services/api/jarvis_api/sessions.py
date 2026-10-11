"""Persistent session/message routes. Local-development API only."""
import os
import uuid
from datetime import datetime

import psycopg
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


def require_local_token(authorization: str | None = Header(default=None)) -> None:
    """Fail closed if a local token is not configured."""
    import hmac

    token = os.getenv("JARVIS_API_TOKEN")
    if not token or not authorization or not hmac.compare_digest(authorization, f"Bearer {token}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def db_url() -> str:
    url = os.getenv("JARVIS_DATABASE_URL")
    if not url:
        raise HTTPException(status_code=503, detail="Database not configured")
    return url


class SessionCreate(BaseModel):
    title: str = Field(default="Nueva conversación", min_length=1, max_length=200)


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime


class MessageCreate(BaseModel):
    client_message_id: uuid.UUID
    content: str = Field(min_length=1, max_length=20000)


class MessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    client_message_id: uuid.UUID | None
    created_at: datetime


@router.post("", response_model=SessionOut, status_code=201, dependencies=[Depends(require_local_token)])
def create_session(payload: SessionCreate):
    session_id = uuid.uuid4()
    with psycopg.connect(db_url()) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sessions (id, title) VALUES (%s, %s) RETURNING id, title, created_at",
            (session_id, payload.title),
        )
        row = cur.fetchone()
    return SessionOut(id=row[0], title=row[1], created_at=row[2])


@router.get("/{session_id}", response_model=SessionOut, dependencies=[Depends(require_local_token)])
def get_session(session_id: uuid.UUID):
    with psycopg.connect(db_url()) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, title, created_at FROM sessions WHERE id = %s", (session_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(id=row[0], title=row[1], created_at=row[2])


@router.post(
    "/{session_id}/messages",
    response_model=MessageOut,
    status_code=201,
    dependencies=[Depends(require_local_token)],
)
def add_message(session_id: uuid.UUID, payload: MessageCreate):
    # Same client_message_id replays return the original message; no duplicate side effects.
    with psycopg.connect(db_url()) as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM sessions WHERE id = %s", (session_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Session not found")
        message_id = uuid.uuid4()
        cur.execute(
            """
            INSERT INTO messages (id, session_id, role, content, client_message_id)
            VALUES (%s, %s, 'user', %s, %s)
            ON CONFLICT (session_id, client_message_id) DO NOTHING
            RETURNING id, session_id, role, content, client_message_id, created_at
            """,
            (message_id, session_id, payload.content, payload.client_message_id),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """SELECT id, session_id, role, content, client_message_id, created_at
                   FROM messages WHERE session_id = %s AND client_message_id = %s""",
                (session_id, payload.client_message_id),
            )
            row = cur.fetchone()
            if row[3] != payload.content:
                raise HTTPException(status_code=409, detail="client_message_id reused with different content")
    return MessageOut(
        id=row[0], session_id=row[1], role=row[2],
        content=row[3], client_message_id=row[4], created_at=row[5],
    )


@router.get(
    "/{session_id}/messages",
    response_model=list[MessageOut],
    dependencies=[Depends(require_local_token)],
)
def list_messages(session_id: uuid.UUID, limit: int = 50):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    with psycopg.connect(db_url()) as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM sessions WHERE id = %s", (session_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Session not found")
        cur.execute(
            """SELECT id, session_id, role, content, client_message_id, created_at
               FROM messages WHERE session_id = %s
               ORDER BY created_at ASC, id ASC LIMIT %s""",
            (session_id, limit),
        )
        rows = cur.fetchall()
    return [
        MessageOut(
            id=row[0], session_id=row[1], role=row[2],
            content=row[3], client_message_id=row[4], created_at=row[5],
        )
        for row in rows
    ]
