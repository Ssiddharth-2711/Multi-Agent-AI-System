from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]



llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
)


def build_search_agent():
    return create_agent(
        model = llm,
        tools= [web_search]
    )


def build_reader_agent():
    return create_agent(
        model = llm,
        tools = [scrape_url]
    )


writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a concise research writer. "
        "Write factual, structured reports without repetition."
    ),
    (
        "human",
        """Create a research report on:

Topic: {topic}

Research:
{research}

Use exactly this structure:

## Introduction
Brief introduction.

## Key Findings
Give 3 important findings with short explanations.

## Conclusion
Summarize the findings.

## Sources
List the available URLs.

Keep the report concise and informative."""
    ),
])

writer_chain = writer_prompt | llm | StrOutputParser()


critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a research report reviewer. "
        "Give simple and useful feedback."
    ),
    (
        "human",
        """Review this research report:

{report}

Give:

Score: X/10

Strengths:
- 2 points

Improvements:
- 2 points

Verdict:
One short sentence."""
    ),
])

critic_chain = critic_prompt | llm | StrOutputParser()







