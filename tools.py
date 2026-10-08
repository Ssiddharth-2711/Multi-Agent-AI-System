
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------
# Tavily client
# ---------------------------------------------------------

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing. "
        "Please add it to your .env file."
    )

tavily = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def web_search(query: str) -> str:
    """Search the web for reliable information."""
    results = tavily.search(query=query, max_results=3)

    out = []

    for r in results["results"]:
        out.append(
            f"Title: {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Snippet: {r['content'][:150]}"
        )

    return "\n---\n".join(out)



@tool
def scrape_url(url: str) -> str:
    """
    Scrape a web page and return clean text content.
    """

    try:
        if not url.startswith(("http://", "https://")):
            return "Invalid URL. Please provide a complete http/https URL."

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.36"
                )
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unnecessary HTML elements
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        if not text:
            return "No readable text was found on this page."

        # Limit content passed to the LLM
        return text[:6000]

    except requests.exceptions.Timeout:
        return "Could not scrape URL: request timed out."

    except requests.exceptions.HTTPError as e:
        return f"Could not scrape URL: HTTP error - {e}"

    except requests.exceptions.RequestException as e:
        return f"Could not scrape URL: request failed - {e}"

    except Exception as e:
        return f"Could not scrape URL: {str(e)}"
