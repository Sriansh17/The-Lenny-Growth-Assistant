"""
Agent Layer

This module provides the agentic orchestration for The Lenny Growth Assistant.

Architecture:
- AnthropicAgent: Uses Anthropic's tool-use API for autonomous RAG with
  search, essay generation, and artifact creation tools.
- The AgentService (in services/agent.py) wraps this layer and handles
  session management, persistence, and fallback to direct LLM calls.

When LLM_PROVIDER=anthropic, the AnthropicAgent handles tool routing.
When LLM_PROVIDER=ollama or openai, the AgentService uses manual routing
with the SkillRegistry for equivalent behavior.
"""
from app.agents.anthropic_agent import AnthropicAgent, get_anthropic_agent

__all__ = ["AnthropicAgent", "get_anthropic_agent"]
