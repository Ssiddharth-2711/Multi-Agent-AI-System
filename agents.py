
import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# STREAMLIT CLOUD SECRETS
# --------------------------------------------------

try:
    import streamlit as st

    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

except Exception:
    pass


# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tools import web_search, scrape_url


# --------------------------------------------------
# LLM CONFIGURATION
# --------------------------------------------------

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.2,
    max_retries=2,
)


# --------------------------------------------------
# SEARCH AGENT
# --------------------------------------------------

def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="""
You are the ResearchMind Search Agent.

Search for useful, reliable information about the user's topic.

Rules:
1. Always call the web_search tool.
2. Preserve the exact titles, URLs, and snippets returned by the tool.
3. Never invent facts, source names, or URLs.
4. Do not replace actual URLs with source names.
5. Do not write a research report.
6. Clearly separate each search result.
7. If the tool returns no usable URLs, say so.
8. Return the original tool output as faithfully as possible.
""",
    )


# --------------------------------------------------
# READER AGENT
# --------------------------------------------------

def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="""
You are the ResearchMind Reader Agent.

Your task is to extract useful information from a source URL
provided in the user's message.

Rules:
1. Call scrape_url using the supplied URL.
2. Summarize the extracted page accurately.
3. Preserve the exact source URL provided by the user.
4. Never invent facts, quotations, statistics, or URLs.
5. Clearly identify information that could not be retrieved.
6. Do not pretend a page was successfully read if scraping failed.
""",
    )


# --------------------------------------------------
# WRITER CHAIN
# --------------------------------------------------

writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an accurate and evidence-focused research writer.

Rules:
1. Use the supplied research as your factual basis.
2. Never invent facts, statistics, dates, citations, or URLs.
3. Preserve actual source URLs exactly as supplied.
4. Use Markdown links for sources.
5. Place source links near relevant factual claims when possible.
6. Distinguish facts from opinions and uncertain claims.
7. Do not claim that a URL was verified unless verification
   evidence is supplied.
8. Use relevant images only if actual image URLs are provided.
9. Never turn an ordinary webpage URL into an image URL.
10. State important research limitations honestly.
"""
    ),
    (
        "human",
        """
Create a research report on:

Topic: {topic}

Research:
{research}

Use this structure:

## Introduction
Introduce the topic and explain its importance.

## Key Findings
Present three important findings with clear explanations.
Support factual claims with the available research and source links.

## Conclusion
Summarize the main findings without introducing unsupported claims.

## Sources
List actual source titles and URLs supplied in the research.
Format links as:
- [Source title](https://actual-url-from-research)

Never invent or guess URLs.
If no source URLs are supplied, state that clearly.

## Relevant Images
Include relevant images only when actual image URLs are supplied.
Use Markdown image syntax:
![Descriptive caption](actual-image-url)

Never invent image URLs. If none are supplied, state that clearly.

## Research Limitations
Identify missing evidence, conflicting information, and
important uncertainties.

Keep the report clear, professional, and informative.
"""
    ),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# --------------------------------------------------
# CRITIC CHAIN
# --------------------------------------------------

critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are ResearchMind's strict research quality reviewer.

Evaluate the supplied report honestly. Do not award high scores
merely because the report is well formatted.

SCORING: 10 POINTS TOTAL

1. Factual support and accuracy: 0-2
2. Research depth and relevance: 0-2
3. Source URLs and citations: 0-2
4. Relevant images and visual support: 0-2
5. Structure, clarity, and completeness: 0-2

Review rules:
- Explain the evidence behind each score.
- Penalize unsupported claims and missing citations.
- A source name without a URL is not a clickable citation.
- A URL in the report does not prove that the link works.
- Do not claim to have opened or verified URLs unless verification
  evidence is provided.
- An image reference does not prove that an image loads.
- Assess image use fairly; not every topic requires images.
- Never invent sources, links, or verification results.
- Provide specific, actionable recommendations.
- Distinguish missing evidence from a proven factual error.
"""
    ),
    (
        "human",
        """
Review this research report:

{report}

Return your review in this format:

## Critic Review

**Overall Score: X/10**

**Score Breakdown**
- Factual support and accuracy: X/2 — explanation
- Research depth and relevance: X/2 — explanation
- Source URLs and citations: X/2 — explanation
- Images and visual support: X/2 — explanation
- Structure and completeness: X/2 — explanation

**Strengths**
- Two specific strengths.

**Problems Found**
- Identify missing or weak citations.
- Identify missing or weak image references when relevant.
- Identify unsupported claims and research gaps.

**Recommended Improvements**
- Three specific improvements, ordered by priority.

**Link and Image Verification**
- Source URLs present: Yes / No
- Image references present: Yes / No
- Link accessibility: Not verified unless evidence is provided.
- Image accessibility: Not verified unless evidence is provided.

**Verdict**
One concise sentence describing the report's quality.
"""
    ),
])

critic_chain = critic_prompt | llm | StrOutputParser()
