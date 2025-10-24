from pydantic import BaseModel, Field


class AdvanceChatRequest(BaseModel):
    """Request model for PD Advance AI agent chatbot interactions."""

    message: str | None = Field(default=None, description="The message to AI agent")
    session_id: str | None = Field(default=None, description="Session ID for the conversation")
    incident_id: str | None = Field(default=None, description="The incident ID associated with the request")
    timestamp: str | None = Field(default=None, description="Timestamp of the request")


class AdvanceChatResponse(BaseModel):
    """Response model from PD Advance AI agent chatbot interactions."""

    message: str | None = Field(default=None, description="The AI agent's response message")
    incident_id: str | None = Field(default=None, description="The incident ID associated with the response")
    session_id: str | None = Field(default=None, description="Session ID for the conversation")
    timestamp: str | None = Field(default=None, description="Timestamp of the request")
    user_id: str | None = Field(default=None, description="The user ID who made the request")
