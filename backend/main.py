
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain
)

import json
import traceback


app = FastAPI(
    title="Multi-Agent Research API",
    description="AI Research System using LangChain, Groq and Tavily",
    version="2.1"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str


@app.get("/")
def home():
    return {
        "message": "Multi-Agent Research API is running 🚀"
    }


def sse_event(event_type, data):
    payload = {
        "type": event_type,
        "data": data
    }

    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def get_error_message(error):
    """
    Convert Groq/API errors into a user-friendly message.
    """

    error_text = str(error)

    if "rate_limit_exceeded" in error_text or "Rate limit reached" in error_text:
        return (
            "⚠️ Groq token limit reached. "
            "Please wait for the limit to reset and try again."
        )

    if "401" in error_text or "authentication" in error_text.lower():
        return (
            "❌ Groq authentication failed. "
            "Please check your GROQ_API_KEY."
        )

    if "TAVILY" in error_text.upper():
        return (
            "❌ Tavily search failed. "
            "Please check your TAVILY_API_KEY."
        )

    return f"❌ Research failed: {error_text}"


def research_stream(topic: str):

    try:

        # ------------------------------------------------
        # START
        # ------------------------------------------------

        yield sse_event(
            "start",
            {
                "message": "Research started",
                "topic": topic
            }
        )


        # ------------------------------------------------
        # SEARCH AGENT
        # ------------------------------------------------

        yield sse_event(
            "progress",
            {
                "agent": "search",
                "status": "working",
                "message": "🔎 Search Agent is searching the web..."
            }
        )

        search_agent = build_search_agent()

        search_result = search_agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"""
Find recent, reliable and detailed
information about:

{topic}
"""
                    )
                ]
            }
        )

        search_results = search_result["messages"][-1].content

        yield sse_event(
            "progress",
            {
                "agent": "search",
                "status": "complete",
                "message": "✅ Search Agent completed.",
                "result": search_results
            }
        )


        # ------------------------------------------------
        # READER AGENT
        # ------------------------------------------------

        yield sse_event(
            "progress",
            {
                "agent": "reader",
                "status": "working",
                "message": "📖 Reader Agent is reading the best source..."
            }
        )

        reader_agent = build_reader_agent()

        reader_result = reader_agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"""
Based on the following search results
about "{topic}", pick the most relevant
URL and scrape it for deeper information.

Search Results:

{search_results[:800]}
"""
                    )
                ]
            }
        )

        scraped_content = reader_result["messages"][-1].content

        yield sse_event(
            "progress",
            {
                "agent": "reader",
                "status": "complete",
                "message": "✅ Reader Agent completed.",
                "result": scraped_content
            }
        )


        # ------------------------------------------------
        # WRITER
        # ------------------------------------------------

        yield sse_event(
            "progress",
            {
                "agent": "writer",
                "status": "working",
                "message": "✍️ Writer is preparing the research report..."
            }
        )

        research_combined = f"""
SEARCH RESULTS:

{search_results}

DETAILED SCRAPED CONTENT:

{scraped_content}
"""

        report = writer_chain.invoke(
            {
                "topic": topic,
                "research": research_combined
            }
        )

        yield sse_event(
            "progress",
            {
                "agent": "writer",
                "status": "complete",
                "message": "✅ Writer completed the report."
            }
        )


        # ------------------------------------------------
        # CRITIC
        # ------------------------------------------------

        yield sse_event(
            "progress",
            {
                "agent": "critic",
                "status": "working",
                "message": "🧐 Critic is reviewing the report..."
            }
        )

        feedback = critic_chain.invoke(
            {
                "report": report
            }
        )

        yield sse_event(
            "progress",
            {
                "agent": "critic",
                "status": "complete",
                "message": "✅ Critic completed the review.",
                "feedback": feedback
            }
        )


        # ------------------------------------------------
        # COMPLETE
        # ------------------------------------------------

        yield sse_event(
            "complete",
            {
                "topic": topic,
                "search_results": search_results,
                "scraped_content": scraped_content,
                "report": report,
                "feedback": feedback
            }
        )


    except Exception as error:

        print("\nERROR IN RESEARCH PIPELINE:")
        traceback.print_exc()

        friendly_message = get_error_message(error)

        yield sse_event(
            "error",
            {
                "message": friendly_message
            }
        )


@app.post("/research/stream")
def research_stream_endpoint(request: ResearchRequest):

    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Research topic cannot be empty."
        )

    return StreamingResponse(
        research_stream(topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

