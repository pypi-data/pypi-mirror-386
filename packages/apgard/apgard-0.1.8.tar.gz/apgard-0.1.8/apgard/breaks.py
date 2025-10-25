from dataclasses import dataclass
from typing import Optional, Dict
import logging

logger = logging.getLogger("apgard")


@dataclass
class BreakStatus:
    break_due: bool
    session_minutes: int
    minutes_until_break: Optional[int] = None
    message: Optional[str] = None
    session_id: Optional[str] = None


class BreakClient:
    def __init__(self, http, break_interval_minutes: int):
        self._http = http  # Should be httpx.Client
        self.break_interval = break_interval_minutes

    def record_activity(self, user_id: str, metadata: Optional[Dict] = None) -> BreakStatus:
        try:
            resp = self._http.post("/api/sessions/activity", json={
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
            return BreakStatus(
                break_due=True,
                session_minutes=0,
                message="Unable to verify session. Please take a break."
            )

    def check_break_status(self, user_id: str) -> BreakStatus:
        try:
            resp = self._http.get(f"/api/sessions/{user_id}/status")
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

    def end_session(self, user_id: str) -> bool:
        try:
            resp = self._http.post(f"/api/sessions/{user_id}/end", json={})
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False
