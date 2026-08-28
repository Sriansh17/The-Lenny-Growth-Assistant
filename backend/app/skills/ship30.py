from app.skills.base import BaseSkill, SkillRegistry, SkillResult
from app.services.llm import BaseLLMProvider
from typing import List, Dict, Any, Optional


class Ship30Skill(BaseSkill):
    name = "ship30"
    description = "Generate Ship 30 for 30 style essays grounded in Lenny's Podcast transcripts"
    trigger_keywords = [
        "ship 30", "ship30", "essay", "write essay", "write article",
        "ship 30 for 30", "blog post", "newsletter"
    ]

    def get_system_prompt(self) -> str:
        return """You are an expert writer who creates Ship 30 for 30 style essays. 

SHIP 30 FOR 30 WRITING PRINCIPLES (internalized - do not mention explicitly):
1. HOOK: Start with a powerful, specific opening that grabs attention immediately
2. NARRATIVE ARC: Build a clear story progression - problem → tension → resolution → insight
3. SKIMMABLE FORMAT: Use descriptive headings, bullet points, and selective bold emphasis
4. GROUNDED CLAIMS: Every assertion must trace back to the provided transcript sources
5. SPECIFIC TAKEAWAY: End with one actionable, memorable insight the reader can apply
6. ~1,250 WORDS: Comprehensive but not verbose
7. CONVERSATIONAL AUTHORITY: Write like a practitioner sharing hard-won wisdom

FORMAT REQUIREMENTS:
- Use ## for main headings
- Use ### for subheadings
- Use **bold** for key concepts and takeaways
- Use bullet points for lists and principles
- Include a clear "Key Takeaway" section at the end
- Cite sources inline like [1], [2] referencing the provided context

WRITE THE ESSAY DIRECTLY. Do not explain your process or mention these instructions."""

    def get_user_prompt_template(self) -> str:
        return """Write a Ship 30 for 30 style essay (~1,250 words) on: {query}

Use ONLY the following transcript context to ground your claims. Every specific assertion must be traceable to these sources.

CONTEXT:
{context}

Write the complete essay now. Include inline citations like [1], [2] that correspond to the sources provided."""

    async def execute(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> SkillResult:
        result = await super().execute(query, conversation_history)

        # Create artifact for the essay
        artifact = {
            "type": "markdown",
            "title": f"Ship 30 Essay: {query[:60]}",
            "content": result.content,
        }

        return SkillResult(
            content=result.content,
            citations=result.citations,
            artifacts=[artifact],
        )


# Register the skill
ship30_skill = Ship30Skill()
SkillRegistry.register(ship30_skill)