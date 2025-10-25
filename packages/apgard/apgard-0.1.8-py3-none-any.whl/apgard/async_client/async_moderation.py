from typing import Optional, Dict
import logging
import httpx
from ..errors import APIError, ValidationError
from ..moderation import ModerationResult

logger = logging.getLogger("apgard")


class AsyncModerationClient:
    MAX_CONTENT_SIZE = 50000  # 50KB

    def __init__(self, http: httpx.AsyncClient):
        self._http = http  # must be an AsyncClient

    async def start_conversation(self, user_id: str) -> str:
        """
        Starts a new conversation for a user and returns the conversation ID.
        The client only ever sees the conversation ID.
        """
        payload = {"user_id": user_id} if user_id else {}
        try:
            resp = await self._http.post("/api/conversations/start", json=payload)
            resp.raise_for_status()
            data = resp.json()
            conversation_id = data["conversation_id"]
            logger.info(f"Started conversation {conversation_id} for user {user_id}")
            return conversation_id
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP error starting conversation: {e}") from e
        except Exception as e:
            raise APIError(f"Failed to start conversation: {e}") from e

    async def moderate_message(
        self,
        user_id: str,
        conversation_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict] = None,
    ) -> ModerationResult:
        """
        Moderates a message within a conversation.
        Threads are managed internally by Apgard; client only provides conversation ID.
        """
        if role not in ("user", "assistant"):
            raise ValidationError("role must be 'user' or 'assistant'")

        if len(content) > self.MAX_CONTENT_SIZE:
            raise ValidationError(f"Content exceeds {self.MAX_CONTENT_SIZE} chars")

        payload = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "content_type": "text",
        }

        if metadata:
            payload["metadata"] = metadata

        try:
            resp = await self._http.post("/api/conversations/message", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP error during moderation request: {e}") from e
        except Exception as e:
            raise APIError(f"Moderation request failed: {e}") from e

        result = ModerationResult(
            message_id=data["message_id"],
            thread_id=data["thread_id"],
            should_intervene=data["should_intervene"],
            reason_codes=data.get("reason_codes", []),
            guiding_message=data.get("guiding_message"),
        )
        logger.info(f"Moderated message {result.message_id}: should_intervene {result.should_intervene}")
        return result
