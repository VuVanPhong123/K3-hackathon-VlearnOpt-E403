from __future__ import annotations

from app.domain.intents import Intent


class QueryPlanner:
    def plan(self, message: str, intent: Intent) -> list[str]:
        if intent in {Intent.COMPARE, Intent.FIND_LOCATION}:
            parts = [part.strip(" ?.,") for part in message.replace(" và ", "|").replace(" and ", "|").split("|")]
            return [part for part in parts if part][:2] or [message]
        return [message]
