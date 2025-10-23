"""
Module for the tests
"""

import os

import pytest

from scrapegraphai.graphs import SmartScraperGraph


@pytest.fixture
def sample_text():
    """
    Example of text fixture.
    """
    file_name = "inputs/plain_html_example.txt"
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, file_name)

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    return text


@pytest.fixture
def graph_config():
    """
    Configuration of the graph fixture.
    """
    return {
        "llm": {
            "model": "ollama/mistral",
            "temperature": 0,
            "format": "json",
            "base_url": "http://localhost:11434",
        }
    }


def test_scraping_pipeline(sample_text, graph_config):
    """
    Test the SmartScraperGraph scraping pipeline.
    """
    smart_scraper_graph = SmartScraperGraph(
        prompt="List me all the news with their description.",
        source=sample_text,
        config=graph_config,
    )

    result = smart_scraper_graph.run()

    assert result is not None
    # Additional assertions to check the structure of the result can be added here
    assert isinstance(result, dict)  # Assuming the result is a dictionary
    assert "news" in result  # Assuming the result should contain a key "news"
