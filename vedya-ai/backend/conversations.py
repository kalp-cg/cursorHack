"""Conversation persistence for follow-up clinical questions."""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import HTTPException

from auth import ensure_uuid


def create_conversation(db, user_id: str, title: str, locale: str = "en") -> str:
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO conversations (user_id, title, locale)
        VALUES (%s, %s, %s)
        RETURNING conversation_id::text
        """,
        (user_id, title[:200] if title else "Clinical case", locale),
    )
    cid = cur.fetchone()[0]
    db.commit()
    cur.close()
    return cid


def assert_conversation_owner(db, conversation_id: str, user_id: str) -> dict[str, Any]:
    cid = ensure_uuid(conversation_id, "conversation_id")
    cur = db.cursor()
    cur.execute(
        """
        SELECT conversation_id::text, user_id::text, title, locale
        FROM conversations WHERE conversation_id = %s
        """,
        (cid,),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if row[1] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this conversation")
    return {"conversation_id": row[0], "user_id": row[1], "title": row[2], "locale": row[3]}


def add_message(
    db,
    conversation_id: str,
    role: str,
    content_text: str,
    payload: Optional[dict[str, Any]] = None,
) -> str:
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO conversation_messages (conversation_id, role, content_text, payload)
        VALUES (%s, %s, %s, %s::jsonb)
        RETURNING message_id::text
        """,
        (conversation_id, role, content_text, json.dumps(payload) if payload is not None else None),
    )
    mid = cur.fetchone()[0]
    cur.execute(
        "UPDATE conversations SET updated_at = NOW() WHERE conversation_id = %s",
        (conversation_id,),
    )
    db.commit()
    cur.close()
    return mid


def list_conversations(db, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
    cur = db.cursor()
    cur.execute(
        """
        SELECT conversation_id::text, title, locale, created_at, updated_at
        FROM conversations
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    return [
        {
            "conversation_id": r[0],
            "title": r[1],
            "locale": r[2],
            "created_at": r[3].isoformat() if r[3] else None,
            "updated_at": r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]


def get_messages(db, conversation_id: str, user_id: str) -> list[dict[str, Any]]:
    assert_conversation_owner(db, conversation_id, user_id)
    cur = db.cursor()
    cur.execute(
        """
        SELECT message_id::text, role, content_text, payload, created_at
        FROM conversation_messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conversation_id,),
    )
    rows = cur.fetchall()
    cur.close()
    out = []
    for r in rows:
        payload = r[3]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = None
        out.append(
            {
                "message_id": r[0],
                "role": r[1],
                "content_text": r[2],
                "payload": payload,
                "created_at": r[4].isoformat() if r[4] else None,
            }
        )
    return out


def build_followup_context(db, conversation_id: str, new_text: str) -> str:
    """Merge prior user turns with the new question for re-ranking."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT content_text FROM conversation_messages
        WHERE conversation_id = %s AND role = 'user'
        ORDER BY created_at ASC
        LIMIT 20
        """,
        (conversation_id,),
    )
    prior = [r[0] for r in cur.fetchall()]
    cur.close()
    parts = prior + [new_text]
    return " | Follow-up: ".join(parts)
