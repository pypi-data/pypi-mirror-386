from typing import Optional, Dict
from ..breaks import BreakStatus
import logging

logger = logging.getLogger("apgard")


class AsyncBreakClient:
    def __init__(self, http, break_interval_minutes: int):
        self._http = http
        self.break_interval = break_interval_minutes

    async def record_activity(self, user_id: str, metadata: Optional[Dict] = None) -> BreakStatus:
        try:
            resp = await self._http.post("/api/sessions/activity", json={
                "user_id": user_id,
                "break_time_minutes": self.break_interval,
                "metadata": metadata
            })
            resp.raise_for_status()
            data = resp.json()
            return BreakStatus(
                break_due=data["break_due"],
                session_minutes=data.get("session_duration_minutes", 0),
                minutes_until_break=data.get("time_until_break_minutes"),
                message=data.get("message"),
                session_id=data.get("session_id")
            )
        except Exception as e:
            logger.error(f"Activity tracking failed: {e}")
            return BreakStatus(break_due=True, session_minutes=0, message="Unable to verify session. Please take a break.")

    async def check_break_status(self, user_id: str) -> BreakStatus:
        try:
            resp = await self._http.get(f"/api/sessions/{user_id}/status")
            resp.raise_for_status()
            data = resp.json()
            return BreakStatus(
                break_due=data["break_due"],
                session_minutes=data.get("session_duration_minutes", 0),
                minutes_until_break=data.get("time_until_break_minutes"),
                session_id=data.get("session_id")
            )
        except Exception as e:
            logger.error(f"Failed to get break status: {e}")
            return BreakStatus(break_due=False, session_minutes=0)

    async def end_session(self, user_id: str) -> bool:
        try:
            await self._http.post(f"/api/sessions/{user_id}/end", json={})
            return True
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False
