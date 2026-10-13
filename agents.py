
import os
from dotenv import load_dotenv

load_dotenv()

# Load the API key from Streamlit Cloud Secrets when available
try:
    import streamlit as st

    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

from langchain.agents import create_agent

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url

# Gemini model

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.2,
    max_retries=2,
)




def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a web research agent. "
            "Call web_search once, then summarize its results briefly. "
            "Do not repeat tool calls."
        ),
    )


def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a webpage reader. "
            "Call scrape_url once for the provided URL, "
            "then summarize the extracted content."
        ),
    )



writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a reliable research writer.
        Use only information supported by the provided research.
        Never invent facts, statistics, dates, or URLs.
        If information is uncertain or sources conflict, state that clearly.
        Avoid repetition and unsupported claims."""
    ),
    (
        "human",
        """Create a research report on:

Topic: {topic}

Research:
{research}

Use exactly this structure:

## Introduction
Introduce the topic and its importance.

## Key Findings
Present 3 important findings with clear explanations.
Support each finding with the available research.

## Conclusion
Summarize the main findings.

## Sources
List only URLs actually provided in the research.
Do not invent URLs. If none are available, state
"No source URLs were provided."

Keep the report clear, concise, and informative."""
    ),
])

writer_chain = writer_prompt | llm | StrOutputParser()




critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a strict but constructive research report reviewer.
        Evaluate factual support, relevance, clarity, structure,
        source quality, and completeness.
        Do not assume unsupported claims are true."""
    ),
    (
        "human",
        """Review this research report:

{report}

Return your review using exactly this format:

Score: X/10

Strengths:
- Two specific strengths.

Improvements:
- Two specific, actionable improvements.

Verdict:
One sentence explaining the report's overall quality."""
    ),
])

critic_chain = critic_prompt | llm | StrOutputParser()
