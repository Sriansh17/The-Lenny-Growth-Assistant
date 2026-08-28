"""
Anthropic Agent Integration Layer

Uses Anthropic's tool-use API to implement an agentic RAG pattern.
The agent has access to tools (retrieval, skill execution) and decides
which to call based on the user's query.

This implements the "agent with tools" pattern from Anthropic's documentation:
- The model receives a system prompt + tools definition
- It decides which tool(s) to call
- Tool results are fed back for final response generation

Reference: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview
"""
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.services.rag import rag_service
from app.services.sanitizer import sanitize_html
import structlog
import json

logger = structlog.get_logger()

# Tool definitions for the Anthropic agent
AGENT_TOOLS = [
    {
        "name": "search_transcripts",
        "description": "Search Lenny's Podcast transcripts for relevant information about product management, growth, strategy, and startup topics. Returns transcript excerpts with source citations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant transcript content"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_ship30_essay",
        "description": "Generate a Ship 30 for 30 style essay (~1250 words) with a strong hook, clear narrative, skimmable formatting, and actionable takeaways. Use this when the user asks for a written essay or long-form content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic for the essay, grounded in transcript knowledge"
                },
                "context": {
                    "type": "string",
                    "description": "Relevant transcript context to base the essay on"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "create_artifact",
        "description": "Create a Markdown or HTML artifact that will be rendered in the app's artifact viewer. Use this for formatted documents, templates, frameworks, or visual content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title for the artifact"
                },
                "content": {
                    "type": "string",
                    "description": "The markdown or HTML content"
                },
                "type": {
                    "type": "string",
                    "enum": ["markdown", "html"],
                    "description": "Type of artifact content"
                }
            },
            "required": ["title", "content", "type"]
        }
    }
]

SYSTEM_PROMPT = """You are The Lenny Growth Assistant, an AI assistant specialized in product management and growth strategy, grounded in Lenny's Podcast transcripts.

CORE BEHAVIOR:
1. Always search transcripts first before answering product/growth questions
2. Cite sources - reference specific episodes, speakers, and quotes
3. Acknowledge when transcripts don't cover a topic
4. Be practical - give actionable insights
5. Create artifacts when the user wants formatted documents or essays

SKILLS:
- search_transcripts: Use this for every factual question about product/growth topics
- generate_ship30_essay: Use when asked for essays, articles, or long-form content
- create_artifact: Use when the user wants a rendered document (markdown/HTML)

When uncertain, say: "Based on the available transcripts, I don't have enough information to answer this confidently."
"""


class AnthropicAgent:
    """
    Agent that uses Anthropic's tool-use API for orchestrated RAG responses.
    
    Flow:
    1. User message + conversation history → Claude with tools
    2. Claude decides to call search_transcripts, generate_ship30_essay, or create_artifact
    3. Tool results are fed back to Claude
    4. Claude generates final grounded response
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLOUD_MODEL

    async def run(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        Run the agent loop with tool use.
        
        Returns:
            {
                "content": str,          # Final assistant response
                "citations": str | None, # Source citations
                "artifacts": list,       # Generated artifacts
                "tools_used": list,      # Tools that were called
            }
        """
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": user_message})

        artifacts = []
        citations = None
        tools_used = []
        iterations = 0

        while iterations < max_iterations:
            iterations += 1

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=settings.MODEL_MAX_TOKENS,
                temperature=settings.MODEL_TEMPERATURE,
                system=SYSTEM_PROMPT,
                tools=AGENT_TOOLS,
                messages=messages,
            )

            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                # Process all tool uses in this response
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tools_used.append(tool_name)

                        logger.info("agent_tool_call", tool=tool_name, input=tool_input)

                        # Execute the tool
                        result = await self._execute_tool(tool_name, tool_input)

                        # Track citations from search
                        if tool_name == "search_transcripts" and result.get("citations"):
                            citations = result["citations"]

                        # Track artifacts
                        if tool_name == "create_artifact" and result.get("artifact"):
                            artifacts.append(result["artifact"])

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result.get("content", "")),
                        })

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                # Final response - extract text content
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                return {
                    "content": final_text,
                    "citations": citations,
                    "artifacts": artifacts,
                    "tools_used": tools_used,
                    "model": self.model,
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                }
            else:
                # Unexpected stop reason
                break

        # If we hit max iterations, return what we have
        return {
            "content": "I reached my processing limit. Here's what I found so far.",
            "citations": citations,
            "artifacts": artifacts,
            "tools_used": tools_used,
            "model": self.model,
            "tokens_used": 0,
        }

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> Dict[str, Any]:
        """Execute a tool and return structured results."""

        if tool_name == "search_transcripts":
            query = tool_input.get("query", "")
            results = rag_service.retrieve(query)
            context = rag_service.format_context(results)
            citations_text = rag_service.format_citations(results)
            return {
                "content": context,
                "citations": citations_text,
            }

        elif tool_name == "generate_ship30_essay":
            topic = tool_input.get("topic", "")
            # First retrieve relevant context
            results = rag_service.retrieve(topic)
            context = rag_service.format_context(results)
            citations_text = rag_service.format_citations(results)
            return {
                "content": f"Context for essay on '{topic}':\n{context}\n\nSources:\n{citations_text}",
                "citations": citations_text,
            }

        elif tool_name == "create_artifact":
            title = tool_input.get("title", "Untitled")
            content = tool_input.get("content", "")
            artifact_type = tool_input.get("type", "markdown")

            sanitized = None
            if artifact_type == "html":
                sanitized = sanitize_html(content)

            return {
                "content": f"Artifact '{title}' created successfully.",
                "artifact": {
                    "type": artifact_type,
                    "title": title,
                    "content": content,
                    "sanitized_content": sanitized,
                },
            }

        return {"content": f"Unknown tool: {tool_name}"}


def get_anthropic_agent() -> Optional[AnthropicAgent]:
    """Factory function - returns agent only if Anthropic is configured."""
    if settings.ANTHROPIC_API_KEY:
        return AnthropicAgent()
    return None
