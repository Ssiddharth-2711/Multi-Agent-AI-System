
import os
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Read Tavily key from .env first
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# If running on Streamlit Cloud, try its Secrets
if not TAVILY_API_KEY:
    try:
        import streamlit as st
        TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
    except Exception:
        pass

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing. Add it to your local .env "
        "or Streamlit Cloud Secrets."
    )

tavily = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def web_search(query: str) -> str:
    """Search the web for reliable information."""
    results = tavily.search(query=query, max_results=3)
    output = []

    for result in results.get("results", []):
        output.append(
            f"Title: {result.get('title', '')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Snippet: {result.get('content', '')[:150]}"
        )

    return "\n---\n".join(output) if output else "No results found."


@tool
def scrape_url(url: str) -> str:
    """Scrape a web page and return clean text content."""
    try:
        if not url.startswith(("http://", "https://")):
            return "Invalid URL. Please provide a complete HTTP/HTTPS URL."

        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script", "style", "nav", "footer",
            "header", "aside", "form"
        ]):
            tag.decompose()

        page_text = soup.get_text(separator=" ", strip=True)

        if not page_text:
            return "No readable text was found on this page."

        return page_text[:6000]

    except requests.exceptions.Timeout:
        return "Could not scrape URL: request timed out."
    except requests.exceptions.RequestException as error:
        return f"Could not scrape URL: {error}"
    except Exception as error:
        return f"Could not scrape URL: {error}"
