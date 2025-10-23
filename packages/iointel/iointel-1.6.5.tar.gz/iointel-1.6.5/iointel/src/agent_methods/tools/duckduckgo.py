import asyncio
import os
from typing import Any, Dict, List, Optional
import backoff
import primp

try:
    from duckduckgo import DuckDuckGoSearchException
except ImportError:
    DuckDuckGoSearchException = Exception

from iointel.src.utilities.decorators import register_tool
from pydantic import BaseModel, ConfigDict, model_validator


class DuckDuckGoSearchAPIWrapper(BaseModel):
    """Wrapper for DuckDuckGo Search API.

    Free and does not require any setup.
    """

    region: Optional[str] = "wt-wt"
    """
    See https://pypi.org/project/duckduckgo-search/#regions
    """
    safesearch: str = "moderate"
    """
    Options: strict, moderate, off
    """
    timelimit: Optional[str] = "y"
    """
    Options: d, w, m, y
    """
    max_results: int = 5
    backend: str = "html"
    """
    Options: auto, html, lite
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Any:
        """Validate that python package exists in environment."""
        try:
            from duckduckgo_search import DDGS  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "Could not import duckduckgo-search python package. "
                "Please install it with `pip install -U duckduckgo-search`."
            ) from e
        return values

    @backoff.on_exception(
        backoff.expo,
        exception=(DuckDuckGoSearchException,),
        max_tries=5,
        jitter=backoff.random_jitter,
    )
    def _ddgs(
        self, query: str, max_results: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Run query through DuckDuckGo text search and return results."""

        from duckduckgo_search import DDGS

        DDGS_PROXY = os.environ.get("DDGS_HTTP_PROXY")
        DDGS_HTTP_V1 = os.environ.get("DDGS_HTTP_V1", "").lower() == "true"

        with DDGS(proxy=DDGS_PROXY) as ddgs:
            if DDGS_HTTP_V1:
                # By default duckduckgo_search hardcode HTTP2.
                # In case need to use HTTP1 must override the client instance
                # https://github.com/deedy5/duckduckgo_search/blob/main/duckduckgo_search/duckduckgo_search.py#L70
                ddgs.client = primp.Client(
                    headers=ddgs.client.headers,
                    proxy=ddgs.proxy,
                    timeout=ddgs.timeout,
                    cookie_store=True,
                    referer=True,
                    impersonate="random",
                    impersonate_os="random",
                    follow_redirects=False,
                    verify=False,
                    http2_only=False,
                )
            ddgs_gen = ddgs.text(
                query,
                region=self.region,  # type: ignore[arg-type]
                safesearch=self.safesearch,
                timelimit=self.timelimit,
                max_results=max_results or self.max_results,
                backend=self.backend,
            )
            if ddgs_gen:
                return list(ddgs_gen)
        return []

    def results(
        self, query: str, max_results: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Run query through DuckDuckGo and return metadata.

        Args:
            query: The query to search for.
            max_results: The number of results to return.

        Returns:
            A list of dictionaries with the following keys:
                snippet - The description of the result.
                title - The title of the result.
                link - The link to the result.
        """
        results = [
            {"snippet": r["body"], "title": r["title"], "link": r["href"]}
            for r in self._ddgs(query, max_results=max_results)
        ]

        if results is None:
            results = [{"error": "No good DuckDuckGo Search Result was found"}]

        return results


@register_tool
def search_the_web(text: str, max_results: int = 10):
    """
    :param text: Text to search
    :param max_results: How many results to return (from 1 to 20)
    :return: The list of snippets in json format
    """
    return DuckDuckGoSearchAPIWrapper().results(text, max_results=max_results)


@register_tool
async def search_the_web_async(text: str, max_results: int = 10):
    """
    :param text: Text to search
    :param max_results: How many results to return (from 1 to 20)
    :return: The list of snippets in json format
    """
    return await asyncio.to_thread(search_the_web, text=text, max_results=max_results)
