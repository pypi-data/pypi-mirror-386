from .core import web_search

#? Required ------------------------------------------------------------------
_info = "This tool allows you to perform web searches using Google Custom Search API with optional web scraping. The search queries are generated automatically based on the user message using an LLM. Requires Google API key and Search Engine ID."

def _execute(message, history, client, config):
    """Main function to execute the web search tool"""
    return web_search(message, client, config, history)