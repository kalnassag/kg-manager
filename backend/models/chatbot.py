"""Pydantic models for chatbot functionality."""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class LLMSettings(BaseModel):
    """LLM configuration settings."""
    provider: LLMProvider = Field(..., description="LLM provider")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    model: str = Field(..., description="Model name (e.g., 'gpt-4', 'claude-3-sonnet')")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=2000, ge=1, le=128000, description="Maximum tokens to generate")
    base_url: Optional[str] = Field(default=None, description="Base URL for Ollama or custom endpoints")

    class Config:
        schema_extra = {
            "example": {
                "provider": "openai",
                "api_key": "sk-...",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 2000
            }
        }


class SystemPromptConfig(BaseModel):
    """System prompt configuration."""
    custom_prompt: Optional[str] = Field(default=None, description="Custom system prompt override")
    include_schema: bool = Field(default=True, description="Include graph schema in prompt")
    include_examples: bool = Field(default=True, description="Include example queries in prompt")

    class Config:
        schema_extra = {
            "example": {
                "custom_prompt": "You are a helpful assistant that answers questions about product data.",
                "include_schema": True,
                "include_examples": True
            }
        }


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    cypher_query: Optional[str] = Field(default=None, description="Generated Cypher query (for assistant messages)")
    query_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Query results (for assistant messages)")

    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError("role must be 'user', 'assistant', or 'system'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "role": "user",
                "content": "Show me the available products",
                "timestamp": "2025-01-21T10:30:00"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message", min_length=1)
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for multi-turn chat")

    class Config:
        schema_extra = {
            "example": {
                "message": "Show me products matching my criteria",
                "conversation_id": "conv_123"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="Assistant response")
    cypher_query: Optional[str] = Field(default=None, description="Generated Cypher query")
    query_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Raw query results")
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(..., description="Response timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "I found the products matching your criteria...",
                "cypher_query": "MATCH (n:Product) RETURN n LIMIT 50",
                "query_results": [],
                "conversation_id": "conv_123",
                "timestamp": "2025-01-21T10:30:05"
            }
        }


class ConversationHistory(BaseModel):
    """Conversation history model."""
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[ChatMessage] = Field(..., description="List of messages in conversation")
    created_at: datetime = Field(..., description="Conversation creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "messages": [],
                "created_at": "2025-01-21T10:30:00",
                "updated_at": "2025-01-21T10:35:00"
            }
        }


class SaveSettingsRequest(BaseModel):
    """Request to save LLM and prompt settings."""
    llm_settings: LLMSettings
    prompt_config: SystemPromptConfig

    class Config:
        schema_extra = {
            "example": {
                "llm_settings": {
                    "provider": "openai",
                    "api_key": "sk-...",
                    "model": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                "prompt_config": {
                    "custom_prompt": None,
                    "include_schema": True,
                    "include_examples": True
                }
            }
        }
