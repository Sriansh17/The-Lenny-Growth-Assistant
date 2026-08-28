from app.skills.base import BaseSkill, SkillRegistry, SkillResult
from app.services.llm import BaseLLMProvider
from typing import List, Dict, Any, Optional
import re


class ArtifactSkill(BaseSkill):
    name = "artifact"
    description = "Generate Markdown or HTML/CSS artifacts from conversation"
    trigger_keywords = [
        "create artifact", "generate artifact", "make artifact",
        "create markdown", "generate html", "make document",
        "render", "create file", "generate file"
    ]

    def get_system_prompt(self) -> str:
        return """You are an artifact generator that creates polished Markdown documents or complete HTML/CSS snippets.

ARTIFACT GENERATION RULES:
1. Determine the best format (Markdown or HTML/CSS) based on the request
2. For HTML: Create complete, self-contained snippets with embedded CSS
3. For Markdown: Use proper formatting with headings, code blocks, tables
4. Content must be grounded in the conversation context and transcript sources
5. HTML must be safe: NO scripts, NO external resources, NO iframes, NO event handlers
6. Output ONLY the artifact content, wrapped in appropriate code fences

OUTPUT FORMAT:
For Markdown:
```markdown
# Title
Content here...
```

For HTML:
```html
<!DOCTYPE html>
<html>
<head>
<style>
/* CSS here */
</style>
</head>
<body>
<!-- Content here -->
</body>
</html>
```"""

    def get_user_prompt_template(self) -> str:
        return """Generate an artifact based on this request: {query}

Conversation context:
{context}

Create a polished, complete artifact (Markdown or HTML/CSS) that addresses the request. 
Make it visually appealing and well-structured. For HTML, embed all CSS inline."""

    async def execute(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> SkillResult:
        result = await super().execute(query, conversation_history)

        # Parse the artifact from the response
        artifact = self._parse_artifact(result.content)
        if artifact:
            return SkillResult(
                content=f"I've created an artifact for you. You can view it in the artifact panel.",
                citations=result.citations,
                artifacts=[artifact],
            )

        return result

    def _parse_artifact(self, content: str) -> Optional[Dict[str, Any]]:
        # Try to extract markdown code block
        md_match = re.search(r'```markdown\n(.*?)\n```', content, re.DOTALL)
        if md_match:
            return {
                "type": "markdown",
                "title": "Generated Document",
                "content": md_match.group(1).strip(),
            }

        # Try to extract HTML code block
        html_match = re.search(r'```html\n(.*?)\n```', content, re.DOTALL)
        if html_match:
            return {
                "type": "html",
                "title": "Generated Artifact",
                "content": html_match.group(1).strip(),
            }

        # Try generic code block
        code_match = re.search(r'```(?:markdown|html)?\n(.*?)\n```', content, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            if code.startswith("<!DOCTYPE") or code.startswith("<html"):
                return {"type": "html", "title": "Generated Artifact", "content": code}
            else:
                return {"type": "markdown", "title": "Generated Document", "content": code}

        return None


artifact_skill = ArtifactSkill()
SkillRegistry.register(artifact_skill)