from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.services.rag import rag_service, RetrievalResult
from app.services.llm import get_llm_provider, BaseLLMProvider
import structlog

logger = structlog.get_logger()


@dataclass
class SkillResult:
    content: str
    citations: str
    artifacts: List[Dict[str, Any]] = None


class BaseSkill(ABC):
    name: str = ""
    description: str = ""
    trigger_keywords: List[str] = []

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def get_user_prompt_template(self) -> str:
        pass

    def should_trigger(self, message: str) -> bool:
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in self.trigger_keywords)

    def retrieve_context(self, query: str) -> List[RetrievalResult]:
        return rag_service.retrieve(query)

    def format_context(self, results: List[RetrievalResult]) -> str:
        return rag_service.format_context(results)

    def format_citations(self, results: List[RetrievalResult]) -> str:
        return rag_service.format_citations(results)

    async def execute(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> SkillResult:
        context_results = self.retrieve_context(query)
        context = self.format_context(context_results)
        citations = self.format_citations(context_results)

        user_prompt = self.get_user_prompt_template().format(
            query=query,
            context=context,
        )

        messages = conversation_history or []
        messages.append({"role": "user", "content": user_prompt})

        response = await self.llm.generate(
            messages=messages,
            system_prompt=self.get_system_prompt(),
            temperature=0.3,
            max_tokens=4096,
        )

        return SkillResult(
            content=response.content,
            citations=citations,
            artifacts=[],
        )


class SkillRegistry:
    _skills: Dict[str, BaseSkill] = {}

    @classmethod
    def register(cls, skill: BaseSkill) -> None:
        cls._skills[skill.name] = skill
        logger.info("skill_registered", name=skill.name)

    @classmethod
    def get(cls, name: str) -> Optional[BaseSkill]:
        return cls._skills.get(name)

    @classmethod
    def get_all(cls) -> List[BaseSkill]:
        return list(cls._skills.values())

    @classmethod
    def find_triggered(cls, message: str) -> Optional[BaseSkill]:
        for skill in cls._skills.values():
            if skill.should_trigger(message):
                return skill
        return None