"""
LLM Service for Graph-based Question Answering

This service handles:
- Text-to-Cypher query generation
- LLM provider abstraction (OpenAI, Anthropic, Google, Ollama)
- Response formatting
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import httpx

from ..models.chatbot import LLMProvider, LLMSettings, SystemPromptConfig


logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based graph question answering."""

    def __init__(self, settings: LLMSettings, prompt_config: SystemPromptConfig):
        """
        Initialize LLM service.

        Args:
            settings: LLM configuration
            prompt_config: System prompt configuration
        """
        self.settings = settings
        self.prompt_config = prompt_config

    def build_system_prompt(self, graph_schema: Dict[str, Any]) -> str:
        """
        Build system prompt for text-to-Cypher conversion.

        Args:
            graph_schema: Graph schema information

        Returns:
            System prompt string
        """
        if self.prompt_config.custom_prompt:
            base_prompt = self.prompt_config.custom_prompt
        else:
            base_prompt = """You are an expert Neo4j Cypher query generator. Your task is to convert natural language questions into valid Cypher queries.

CRITICAL RULES:
1. Use ONLY the exact node labels, relationship types, and property names provided in the schema
2. DO NOT invent, assume, or hallucinate any relationship names - use EXACTLY what appears in the schema
3. If the schema shows relationship types, those are the ONLY ones that exist
4. Generate ONLY valid Cypher syntax
5. Use MATCH clauses for retrieving data
6. Use WHERE clauses for filtering
7. Return relevant properties using RETURN
8. Limit results to 50 unless specified otherwise
9. Use case-insensitive matching with toLower() when appropriate for user input"""

        schema_section = ""
        if self.prompt_config.include_schema:
            # Build schema section
            labels = graph_schema.get('labels', [])
            relationships = graph_schema.get('relationship_types', [])

            # Format relationship types more prominently
            rel_list = '\n'.join([f"  - {rel}" for rel in relationships]) if relationships else "  (none defined)"

            schema_section = f"""

## Graph Schema (EXACT NAMES - DO NOT MODIFY)

### Available Node Labels:
{', '.join(labels)}

### Available Relationship Types (USE THESE EXACTLY):
{rel_list}

### Property Naming Patterns:
- _id: Unique identifier (required)
- name: Entity name
- Properties often follow patterns like: inside_*, design_*, display_*, camera_*
- For technical specs, check for prefixed properties (e.g., inside_ram_size_gb, inside_cpu_model)
- Brand relationships use the relationship types listed above"""

        examples_section = ""
        if self.prompt_config.include_examples:
            # Generate examples using actual schema
            examples_section = """

## Example Queries:

Question: "What laptops do we have?"
Cypher: MATCH (l:Laptop) RETURN l.name, l._id LIMIT 50

Question: "Find laptops with more than 16GB RAM"
Cypher: MATCH (l:Laptop) WHERE l.inside_ram_size_gb > 16 RETURN l.name, l.inside_ram_size_gb, l._id LIMIT 50

Question: "Show me all brands"
Cypher: MATCH (b:Brand) RETURN b.name LIMIT 50

## CRITICAL Instructions:
1. You MUST use ONLY the relationship types listed in the "Graph Schema" section above
2. DO NOT invent or assume relationship names - use EXACTLY what is shown in the schema
3. The schema shows ALL available relationship types - there are no others
4. If a relationship seems missing, describe the limitation in your response
5. Always use property names that exist in the actual data (check common patterns like inside_*, design_*, etc.)
6. Return ONLY the Cypher query, no explanation
7. Add LIMIT clause to prevent returning too many results"""

        return base_prompt + schema_section + examples_section

    async def generate_cypher(
        self,
        question: str,
        graph_schema: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate Cypher query from natural language question.

        Args:
            question: User's natural language question
            graph_schema: Graph schema information
            conversation_history: Previous conversation messages

        Returns:
            Generated Cypher query string
        """
        system_prompt = self.build_system_prompt(graph_schema)

        # Build conversation context
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-5:])  # Last 5 messages for context

        # Add current question
        messages.append({
            "role": "user",
            "content": f"Convert this question to a Cypher query: {question}"
        })

        # Call appropriate LLM provider
        try:
            if self.settings.provider == LLMProvider.OPENAI:
                cypher = await self._call_openai(system_prompt, messages)
            elif self.settings.provider == LLMProvider.ANTHROPIC:
                cypher = await self._call_anthropic(system_prompt, messages)
            elif self.settings.provider == LLMProvider.GOOGLE:
                cypher = await self._call_google(system_prompt, messages)
            elif self.settings.provider == LLMProvider.OLLAMA:
                cypher = await self._call_ollama(system_prompt, messages)
            else:
                raise ValueError(f"Unsupported provider: {self.settings.provider}")

            # Clean up the response (remove markdown code blocks if present)
            cypher = cypher.strip()
            if cypher.startswith("```"):
                # Remove markdown code blocks
                lines = cypher.split("\n")
                cypher = "\n".join(lines[1:-1]) if len(lines) > 2 else cypher
                cypher = cypher.replace("```cypher", "").replace("```", "").strip()

            return cypher

        except Exception as e:
            logger.error(f"Error generating Cypher: {e}")
            raise

    async def format_response(
        self,
        question: str,
        cypher_query: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Format query results into a natural language response.

        Args:
            question: Original user question
            cypher_query: Cypher query that was executed
            results: Query results

        Returns:
            Natural language response
        """
        system_prompt = """You are a helpful assistant that explains database query results in natural language.

Your task:
1. Take the user's question and the query results
2. Provide a clear, concise answer in natural language
3. If there are many results, summarize them
4. If there are no results, explain that no matches were found
5. Format your response in a friendly, conversational tone"""

        # Format results for context
        results_text = json.dumps(results[:10], indent=2)  # Limit to 10 for token efficiency
        result_count = len(results)

        user_message = f"""Question: {question}

Query Results ({result_count} items):
{results_text}

Please provide a natural language answer to the question based on these results."""

        messages = [{"role": "user", "content": user_message}]

        try:
            if self.settings.provider == LLMProvider.OPENAI:
                response = await self._call_openai(system_prompt, messages)
            elif self.settings.provider == LLMProvider.ANTHROPIC:
                response = await self._call_anthropic(system_prompt, messages)
            elif self.settings.provider == LLMProvider.GOOGLE:
                response = await self._call_google(system_prompt, messages)
            elif self.settings.provider == LLMProvider.OLLAMA:
                response = await self._call_ollama(system_prompt, messages)
            else:
                raise ValueError(f"Unsupported provider: {self.settings.provider}")

            return response

        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            # Fallback to simple formatting
            if result_count == 0:
                return "I didn't find any results matching your question."
            elif result_count == 1:
                return f"I found 1 result: {json.dumps(results[0], indent=2)}"
            else:
                return f"I found {result_count} results. Here are the first few: {json.dumps(results[:3], indent=2)}"

    # ============================================================================
    # Provider-specific methods
    # ============================================================================

    async def _call_openai(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API."""
        api_key = self.settings.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages
            ],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Call Anthropic API."""
        api_key = self.settings.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not configured")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",  # Using stable version
            "Content-Type": "application/json"
        }

        logger.info(f"Calling Anthropic API with model: {self.settings.model}")

        payload = {
            "model": self.settings.model,
            "system": system_prompt,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                logger.error(f"Anthropic API error: {error_detail}")
                try:
                    error_json = e.response.json()
                    error_msg = error_json.get("error", {}).get("message", error_detail)
                except:
                    error_msg = error_detail
                raise ValueError(f"Anthropic API error: {error_msg}")
            except httpx.RequestError as e:
                logger.error(f"Network error calling Anthropic: {e}")
                raise ValueError(f"Network error: {str(e)}")

    async def _call_google(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Call Google Gemini API."""
        api_key = self.settings.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        # Combine system prompt with first user message
        combined_messages = [
            {"role": "user", "parts": [{"text": system_prompt + "\n\n" + messages[0]["content"]}]}
        ]

        payload = {
            "contents": combined_messages,
            "generationConfig": {
                "temperature": self.settings.temperature,
                "maxOutputTokens": self.settings.max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_ollama(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Call Ollama API (local LLM)."""
        base_url = self.settings.base_url or "http://localhost:11434"
        url = f"{base_url}/api/chat"

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages
            ],
            "stream": False,
            "options": {
                "temperature": self.settings.temperature,
                "num_predict": self.settings.max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]


# Singleton instance
_llm_service: Optional[LLMService] = None
_current_settings: Optional[Dict[str, Any]] = None


def get_llm_service(
    settings: Optional[LLMSettings] = None,
    prompt_config: Optional[SystemPromptConfig] = None
) -> Optional[LLMService]:
    """
    Get or create LLM service instance.

    Args:
        settings: LLM settings (required for first initialization)
        prompt_config: Prompt configuration (required for first initialization)

    Returns:
        LLM service instance or None if not configured
    """
    global _llm_service, _current_settings

    # If settings provided, update the service
    if settings is not None and prompt_config is not None:
        settings_dict = {
            "provider": settings.provider.value,
            "model": settings.model,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "custom_prompt": prompt_config.custom_prompt,
            "include_schema": prompt_config.include_schema,
            "include_examples": prompt_config.include_examples
        }

        # Check if settings changed
        if _current_settings != settings_dict:
            _llm_service = LLMService(settings, prompt_config)
            _current_settings = settings_dict
            logger.info(f"LLM service configured with provider: {settings.provider}, model: {settings.model}")

    return _llm_service
