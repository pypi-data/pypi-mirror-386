from typing import Optional, Union
from agno.tools.knowledge import KnowledgeTools as AgnoKnowledgeTools
from .common import make_base, wrap_tool
from agno.agent.agent import Agent
from agno.team.team import Team
from agno.knowledge.agent import AgentKnowledge
from pydantic import Field


class Knowledge(make_base(AgnoKnowledgeTools)):
    knowledge: AgentKnowledge
    instructions: Optional[str] = Field(default=None, frozen=True)
    add_instructions: bool = Field(default=True, frozen=True)
    add_few_shot: bool = Field(default=False, frozen=True)
    few_shot_examples: Optional[str] = Field(default=None, frozen=True)

    def _get_tool(self):
        return self.Inner(
            knowledge=self.knowledge,
            think=True,
            search=True,
            analyze=True,
            instructions=self.instructions,
            add_instructions=self.add_instructions,
            add_few_shot=self.add_few_shot,
            few_shot_examples=self.few_shot_examples,
        )

    @wrap_tool("agno__knowledge__think", AgnoKnowledgeTools.think)
    def think(self, agent: Union[Agent, Team], thought: str) -> str:
        return self._tool.think(agent, thought)

    @wrap_tool("agno__knowledge__search", AgnoKnowledgeTools.search)
    def search(self, agent: Union[Agent, Team], query: str) -> str:
        return self._tool.search(agent, query)

    @wrap_tool("agno__knowledge__analyze", AgnoKnowledgeTools.analyze)
    def analyze(self, agent: Union[Agent, Team], analysis: str) -> str:
        return self._tool.analyze(agent, analysis)
