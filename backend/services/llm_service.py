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

Important rules:
1. Generate ONLY valid Cypher syntax
2. Use MATCH clauses for retrieving data
3. Use WHERE clauses for filtering
4. Return relevant properties using RETURN
5. Limit results to 50 unless specified otherwise
6. Use case-insensitive matching with toLower() when appropriate
7. Handle property names exactly as they appear in the schema"""

        schema_section = ""
        if self.prompt_config.include_schema:
            # Build schema section
            labels = graph_schema.get('labels', [])
            relationships = graph_schema.get('relationship_types', [])

            schema_section = f"""

## Graph Schema

### Node Labels:
{', '.join(labels)}

### Relationship Types:
{', '.join(relationships)}

### Common Properties:
- _id: Unique identifier
- name: Entity name
- brand: Product brand
- price: Product price
- category: Product category"""

        examples_section = ""
        if self.prompt_config.include_examples:
            examples_section = """

## Example Queries:

Question: "What laptops do we have?"
Cypher: MATCH (l:Laptop) RETURN l.name, l.brand, l._id LIMIT 50

Question: "Find laptops with more than 16GB RAM"
Cypher: MATCH (l:Laptop) WHERE l.ram_gb > 16 RETURN l.name, l.brand, l.ram_gb LIMIT 50

Question: "What products are from Apple?"
Cypher: MATCH (p)-[:HAS_BRAND]->(b:Brand {name: 'Apple'}) RETURN p.name, p._id LIMIT 50

Question: "Show me all smartphone brands"
Cypher: MATCH (s:Smartphone)-[:HAS_BRAND]->(b:Brand) RETURN DISTINCT b.name

## Instructions:
1. Analyze the question carefully
2. Identify the entity types and relationships needed
3. Generate a valid Cypher query
4. Return ONLY the Cypher query, no explanation"""

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
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.settings.model,
            "system": system_prompt,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

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
