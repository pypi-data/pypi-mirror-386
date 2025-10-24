import os
import uuid
from datetime import UTC, datetime

from pagerduty_advance_mcp.client import get_client
from pagerduty_advance_mcp.models import (
    AdvanceChatRequest,
    AdvanceChatResponse,
)

API_KEY = os.getenv("PAGERDUTY_USER_API_KEY")
API_HOST = os.getenv("PAGERDUTY_API_HOST", "https://api.pagerduty.com")


async def advance_chat_request(
    advance_chat_data: AdvanceChatRequest,
) -> AdvanceChatResponse:
    """Send message to the PD Advance AI agent for incident resolution.

    Make sure to extract the message and incident ID from user message

    Args:
        advance_chat_data (AdvanceChatRequest): The data for the chat assistant request.

    Returns:
        The AI agent's response
    """
    formatted_timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    complete_request = AdvanceChatRequest(
        session_id=str(uuid.uuid4()),
        timestamp=formatted_timestamp,
        message=advance_chat_data.message,
        incident_id=advance_chat_data.incident_id,
    )

    response = get_client().jpost(
        "/advance/chat", json=complete_request.model_dump(), headers={"X-EARLY-ACCESS": "gen_ai_api_early_access"}
    )

    return AdvanceChatResponse.model_validate(response)
