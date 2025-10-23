from typing import Literal, Optional
from agno.tools.tavily import TavilyTools as AgnoTavilyTools
from .common import make_base, wrap_tool
from pydantic import Field


class Tavily(make_base(AgnoTavilyTools)):
    api_key: Optional[str] = Field(default=None, frozen=True)
    max_tokens: int = Field(default=6000, frozen=True)
    include_answer: bool = Field(default=True, frozen=True)
    search_depth: Literal["basic", "advanced"] = Field(default="advanced", frozen=True)
    format: Literal["json", "markdown"] = Field(default="markdown", frozen=True)

    def _get_tool(self):
        return self.Inner(
            api_key=self.api_key,
            search=True,
            max_tokens=self.max_tokens,
            include_answer=self.include_answer,
            search_depth=self.search_depth,
            format=self.format,
            use_search_context=True,
        )

    @wrap_tool(
        "agno__tavily__web_search_using_tavily", AgnoTavilyTools.web_search_using_tavily
    )
    def web_search_using_tavily(self, query: str, max_results: int = 5) -> str:
        return self._tool.web_search_using_tavily(query, max_results)

    @wrap_tool(
        "agno__tavily__web_search_with_tavily", AgnoTavilyTools.web_search_with_tavily
    )
    def web_search_with_tavily(self, query: str) -> str:
        return self._tool.web_search_with_tavily(query)
