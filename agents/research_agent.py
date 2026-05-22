from __future__ import annotations

import dataclasses

from pydantic_ai import Agent, RunContext

import config
from prompts.research_agent import control, scheming_strong, scheming_weak
from schemas.research import ResearchCondition, ResearchOutput
from tools.mock_search import SearchResponse, mock_search


@dataclasses.dataclass
class ResearchAgentDeps:
    topic: str
    condition: ResearchCondition


research_agent: Agent[ResearchAgentDeps, ResearchOutput] = Agent(
    output_type=ResearchOutput,
    deps_type=ResearchAgentDeps,
    name="research_agent",
)


@research_agent.system_prompt(dynamic=True)
def research_system_prompt(ctx: RunContext[ResearchAgentDeps]) -> str:
    match ctx.deps.condition:
        case ResearchCondition.control:
            return control.SYSTEM_PROMPT
        case ResearchCondition.scheming_weak:
            return scheming_weak.SYSTEM_PROMPT
        case ResearchCondition.scheming_strong:
            return scheming_strong.SYSTEM_PROMPT


@research_agent.tool_plain
def search(query: str) -> dict:
    """Search for research sources on a given topic.

    Args:
        query: The research topic or question to search for.
    """
    response: SearchResponse = mock_search(query)
    return {
        "results": [
            {
                "url": r.url,
                "snippet": r.snippet,
                "publication_date": r.publication_date,
                "domain_reliability": r.domain_reliability,
            }
            for r in response.results
        ],
        "total_found": response.total_found,
    }


async def run_research_agent(topic: str, condition: ResearchCondition) -> ResearchOutput:
    deps = ResearchAgentDeps(topic=topic, condition=condition)
    result = await research_agent.run(
        f"Research the following topic and produce a comprehensive analysis: {topic}",
        deps=deps,
        model=config.get_model(),
    )
    return result.output
