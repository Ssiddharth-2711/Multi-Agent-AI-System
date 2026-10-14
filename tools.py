
import os
import time
import requests
import streamlit as st

from bs4 import BeautifulSoup
from tavily import TavilyClient
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# TAVILY API CONFIGURATION
# --------------------------------------------------

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Fallback to Streamlit Cloud Secrets
if not TAVILY_API_KEY:
    try:
        TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
    except Exception:
        pass

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing. Add it to your local .env "
        "or Streamlit Cloud Secrets."
    )

tavily = TavilyClient(api_key=TAVILY_API_KEY)



# --------------------------------------------------
# WEB SEARCH TOOL
# --------------------------------------------------

@tool
def web_search(query: str) -> str:
    """Search the web and return source titles, actual URLs,
    and snippets for research reports and citations."""

    for attempt in range(3):
        try:
            response = tavily.search(
                query=query,
                max_results=5,
            )

            results = response.get("results", [])
            output = []

            for index, result in enumerate(results, start=1):
                title = result.get("title") or "Untitled source"
                url = result.get("url") or ""
                snippet = result.get("content") or ""

                if not url.startswith(("http://", "https://")):
                    continue

                output.append(
                    f"Source {index}\n"
                    f"Title: {title}\n"
                    f"URL: {url}\n"
                    f"Snippet: {snippet[:500]}\n"
                )

            if not output:
                return (
                    "No usable search results with valid URLs were found."
                )

            return (
                "WEB SEARCH RESULTS\n"
                "Preserve these exact source URLs in the research report. "
                "Do not invent or modify URLs.\n\n"
                + "\n---\n".join(output)
            )

        except Exception as error:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                return (
                    "Search failed after 3 attempts. "
                    f"{type(error).__name__}: {error}"
                )


            if not output:
                return "No search results found for this query."

            return "\n\n---\n\n".join(output)

        except Exception as error:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                return (
                    "Search failed after 3 attempts. "
                    f"Error: {type(error).__name__}: {error}. "
                    "Please check your internet connection and "
                    "Tavily API availability."
                )


# --------------------------------------------------
# WEBPAGE SCRAPING TOOL
# --------------------------------------------------

@tool
def scrape_url(url: str) -> str:
    """Scrape a webpage and return clean text content."""

    try:
        if not url.startswith(("http://", "https://")):
            return (
                "Invalid URL. Please provide a complete "
                "HTTP/HTTPS URL."
            )

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
        ]):
            tag.decompose()

        page_text = soup.get_text(
            separator=" ",
            strip=True,
        )

        if not page_text:
            return "No readable text was found on this page."

        return page_text[:6000]

    except requests.exceptions.Timeout:
        return "Could not scrape URL: request timed out."

    except requests.exceptions.RequestException as error:
        return (
            "Could not scrape URL: "
            f"{type(error).__name__}: {error}"
        )

    except Exception as error:
        return (
            "Could not scrape URL: "
            f"{type(error).__name__}: {error}"
        )
