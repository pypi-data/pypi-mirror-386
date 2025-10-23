import pytest

from iointel import Agent
from iointel.src.agent_methods.tools.firecrawl import Crawler
from iointel.src.utilities.runners import run_agents


async def test_firecrawl():
    crawler = Crawler(timeout=120)
    agent = Agent(
        name="Agent",
        instructions="You are a crawler agent. Crawl web pages, retrieve information, do what user asks.",
        tools=[crawler.scrape_url],
    )
    try:
        result = await run_agents(
            "Crawl this page: https://decrypt.co/306329/io-net-launches-generative-intelligence-platform-for-developers. "
            "What is the exact date of the io-intelligence first release? "
            "Provide the response in a format: dd-mm-yyyy",
            agents=[agent],
        ).execute()
    except Exception as err:
        if "Request timed out" in str(err):
            pytest.xfail(reason=f"Timed out: {err}")
        raise
    assert result is not None, "Expected a result from the agent run."
    assert "17-02-2025" in result
