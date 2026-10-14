
import streamlit as st
import time
import re
import requests

from urllib.parse import urlparse

from io import BytesIO
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)

from xml.sax.saxutils import escape, quoteattr

from agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)

# ---------------------------------------------------------
# Source links and thumbnail helpers
# ---------------------------------------------------------

def extract_sources(search_text):
    """Extract unique source URLs from existing search results."""

    sources = []
    seen_urls = set()

    url_pattern = r'https?://[^\s<>"\']+'

    for match in re.finditer(url_pattern, search_text or ""):
        url = match.group(0).rstrip(".,);]}")

        if url in seen_urls:
            continue

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            continue

        seen_urls.add(url)

        # Try to get a title and snippet from nearby search text.
        line_start = search_text.rfind("\n", 0, match.start()) + 1
        line_end = search_text.find("\n", match.end())

        if line_end == -1:
            line_end = len(search_text)

        current_line = search_text[line_start:line_end].strip()

        previous_start = search_text.rfind(
            "\n", 0, max(0, line_start - 1)
        ) + 1

        previous_line = search_text[
            previous_start:line_start
        ].strip()

        title = parsed.netloc.removeprefix("www.")
        snippet = ""

        if current_line.lower().startswith("title:"):
            title = current_line.split(":", 1)[1].strip()

        elif previous_line.lower().startswith("title:"):
            title = previous_line.split(":", 1)[1].strip()

        if current_line.lower().startswith("snippet:"):
            snippet = current_line.split(":", 1)[1].strip()

        sources.append({
            "title": title or parsed.netloc,
            "url": url,
            "snippet": snippet,
        })

    return sources[:6]


def get_page_thumbnail(url):
    """Get a preview image from a webpage without using an LLM."""

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return None

        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
            stream=True,
        )

        try:
            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if "text/html" not in content_type:
                return None

            response.close()
        finally:
            response.close()

        # Fetch the page HTML to read its preview metadata.
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for attribute in ("og:image", "twitter:image"):
            tag = soup.find("meta", property=attribute)

            if not tag:
                tag = soup.find("meta", attrs={"name": attribute})

            if tag and tag.get("content"):
                image_url = tag["content"].strip()

                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = (
                        f"{parsed.scheme}://{parsed.netloc}"
                        + image_url
                    )

                image_parsed = urlparse(image_url)

                if image_parsed.scheme in ("http", "https"):
                    return image_url

        return None

    except Exception:
        return None



def create_pdf_report(topic, report, sources):
    """Create a downloadable PDF report with clickable source links."""

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#2563eb")

    story = [
        Paragraph("ResearchMind Research Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            f"<b>Research Topic:</b> {escape(topic)}",
            styles["BodyText"],
        ),
        Spacer(1, 18),
    ]

    # Add the report content.
    for line in (report or "").splitlines():
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 6))
        elif stripped.startswith("### "):
            story.append(
                Paragraph(escape(stripped[4:]), styles["Heading3"])
            )
        elif stripped.startswith("## "):
            story.append(
                Paragraph(escape(stripped[3:]), styles["Heading2"])
            )
        elif stripped.startswith("# "):
            story.append(
                Paragraph(escape(stripped[2:]), styles["Heading1"])
            )
        elif stripped.startswith(("- ", "* ")):
            story.append(
                Paragraph(
                    "&#8226; " + escape(stripped[2:]),
                    styles["BodyText"],
                )
            )
        else:
            story.append(
                Paragraph(escape(stripped), styles["BodyText"])
            )

        story.append(Spacer(1, 5))

    # Add clickable source URLs.
    if sources:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Sources", styles["Heading1"]))

        for source in sources:
            title = escape(source.get("title", "Source"))
            url = source.get("url", "")

            if url.startswith(("https://", "http://")):
                story.append(
                    Paragraph(
                        f'{title}<br/><link href="{escape(url)}" '
                        f'color="blue">{escape(url)}</link>',
                        styles["BodyText"],
                    )
                )
                story.append(Spacer(1, 8))

    document.build(story)

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()



st.set_page_config(
    page_title="ResearchMind | Multi-Agent AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 0% 0%, rgba(0,145,255,.20), transparent 28%),
        radial-gradient(circle at 100% 0%, rgba(0,238,255,.14), transparent 25%),
        radial-gradient(circle at 100% 100%, rgba(0,91,255,.18), transparent 30%),
        #020d26;
    color: #eaf7ff;
    min-height: 100vh;
}

.stApp:before,
.stApp:after {
    content: "";
    position: fixed;
    pointer-events: none;
    z-index: 0;
    border-radius: 50%;
    filter: blur(2px);
}

.stApp:before {
    width: 520px;
    height: 150px;
    left: -160px;
    top: -45px;
    border: 2px solid rgba(0,195,255,.45);
    transform: rotate(-25deg);
    box-shadow: 0 0 35px rgba(0,160,255,.30);
}

.stApp:after {
    width: 520px;
    height: 150px;
    right: -160px;
    bottom: -45px;
    border: 2px solid rgba(0,195,255,.40);
    transform: rotate(-25deg);
    box-shadow: 0 0 35px rgba(0,160,255,.25);
}

#MainMenu, header, footer {
    visibility: hidden;
}

.block-container {
    max-width: 1440px;
    padding: 1.2rem 2.2rem 3rem;
    position: relative;
    z-index: 1;
}

/* HERO */
.hero {
    text-align: center;
    padding: 8px 10px 20px;
}

.hero-kicker {
    color: #00d9ff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 5px;
    margin-bottom: 8px;
}

.hero-title {
    margin: 0;
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(48px, 6vw, 76px);
    font-weight: 700;
    line-height: 1;
    letter-spacing: -3px;
    color: white;
    text-shadow: 0 0 30px rgba(0,180,255,.18);
}

.hero-title span {
    background: linear-gradient(90deg,#ffffff 45%,#00d9ff 72%,#008cff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.hero-subtitle {
    max-width: 670px;
    margin: 14px auto 0;
    color: #9fc5ee;
    font-size: 16px;
    line-height: 1.65;
}

/* VISUAL PIPELINE */
.visual-pipeline {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 16px 22px;
    margin: 8px 0 18px;
    border: 1px solid rgba(0,196,255,.75);
    border-radius: 18px;
    background: linear-gradient(135deg,rgba(0,73,150,.28),rgba(0,18,58,.72));
    box-shadow: 0 0 25px rgba(0,167,255,.12), inset 0 0 25px rgba(0,160,255,.04);
}

.pipeline-node {
    min-width: 210px;
    padding: 12px 20px;
    border: 1px solid rgba(0,194,255,.9);
    border-radius: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: linear-gradient(135deg,rgba(0,104,205,.32),rgba(2,28,75,.72));
    box-shadow: 0 0 18px rgba(0,174,255,.15), inset 0 0 15px rgba(0,185,255,.05);
    color: #dff8ff;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
}

.pipeline-icon {
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: linear-gradient(145deg,#008cff,#00dfff);
    box-shadow: 0 0 20px rgba(0,197,255,.45);
    font-size: 19px;
}

.pipeline-arrow {
    color: #42cfff;
    font-size: 32px;
    text-shadow: 0 0 12px #00bfff;
}

/* CARDS */
.ui-card {
    border: 1px solid rgba(0,186,255,.68);
    border-radius: 16px;
    background: linear-gradient(145deg,rgba(2,38,91,.72),rgba(2,20,55,.82));
    box-shadow: 0 12px 35px rgba(0,0,0,.25), inset 0 0 25px rgba(0,150,255,.04);
    padding: 22px;
}

.section-title {
    color: #00e0ff;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.section-title:before {
    content: "";
    display: inline-block;
    width: 36px;
    height: 3px;
    background: #00dfff;
    margin-right: 12px;
    vertical-align: middle;
    box-shadow: 0 0 12px #00cfff;
}

/* INPUT */
.stTextInput > div > div > input {
    background: rgba(0,16,45,.88) !important;
    color: #eafaff !important;
    border: 1px solid #008fda !important;
    border-radius: 11px !important;
    padding: 14px 16px !important;
    font-size: 14px !important;
    box-shadow: inset 0 0 12px rgba(0,151,255,.05);
}

.stTextInput > div > div > input:focus {
    border-color: #00dcff !important;
    box-shadow: 0 0 0 2px rgba(0,215,255,.13), 0 0 20px rgba(0,180,255,.12) !important;
}

.stTextInput label {
    display: none !important;
}

.stButton > button {
    min-height: 50px;
    border: 0 !important;
    border-radius: 11px !important;
    color: #001126 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    background: linear-gradient(100deg,#15e5ee,#008cff) !important;
    box-shadow: 0 8px 28px rgba(0,167,255,.28), 0 0 20px rgba(0,208,255,.12);
    transition: .2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 35px rgba(0,174,255,.42);
}

.try-label {
    color: #00dfff;
    font-weight: 700;
    margin-top: 17px;
    display: inline-block;
}

.chip {
    display: inline-block;
    margin: 10px 5px 0 8px;
    padding: 7px 14px;
    border: 1px solid rgba(0,155,255,.75);
    border-radius: 20px;
    color: #70cfff;
    background: rgba(0,83,160,.16);
    font-size: 12px;
}

/* AGENTS */
.agent-heading {
    color: #00e0ff;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.agent-heading:before {
    content: "";
    display: inline-block;
    width: 36px;
    height: 3px;
    background: #00e0ff;
    margin-right: 12px;
    vertical-align: middle;
    box-shadow: 0 0 12px #00cfff;
}

.agent-card {
    display: flex;
    align-items: center;
    min-height: 56px;
    margin-bottom: 9px;
    padding: 8px 14px;
    border: 1px solid rgba(0,157,230,.55);
    border-radius: 15px;
    background: linear-gradient(90deg,rgba(4,40,89,.82),rgba(2,25,64,.78));
}

.agent-icon {
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 14px;
    border-radius: 50%;
    background: linear-gradient(145deg,#008cff,#00dfff);
    box-shadow: 0 0 17px rgba(0,188,255,.34);
    font-size: 19px;
}

.agent-name {
    color: #eaf7ff;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 14px;
}

.agent-description {
    display: none;
}

.agent-status {
    margin-left: auto;
    padding: 7px 15px;
    border-radius: 18px;
    color: #66cfff;
    background: rgba(0,122,205,.18);
    border: 1px solid rgba(0,154,235,.35);
    font-size: 10px;
    letter-spacing: .8px;
    font-weight: 600;
}

.agent-running {
    border-color: #00d9ff;
    box-shadow: 0 0 22px rgba(0,201,255,.18);
}

.status-running {
    color: #00e8ff;
}

.agent-done {
    border-color: rgba(37,236,211,.65);
}

.status-done {
    color: #45f0d6;
}

.agent-waiting {
    opacity: 1;
}

.loading-dot {
    animation: blink 1s infinite;
}

@keyframes blink {
    0%,100% { opacity: .3; }
    50% { opacity: 1; }
}

/* PROGRESS */
.progress-container {
    margin-top: 10px;
    padding: 13px 16px;
    border: 1px solid rgba(0,157,230,.55);
    border-radius: 13px;
    background: rgba(1,26,64,.7);
}

.progress-label {
    display: flex;
    justify-content: space-between;
    color: #00dfff;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
}

.progress-track {
    height: 7px;
    border-radius: 10px;
    background: #0b315e;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg,#00dfff,#008cff);
    box-shadow: 0 0 12px rgba(0,216,255,.55);
}

/* RESULTS */
.results-line {
    height: 1px;
    background: linear-gradient(90deg,#00dfff,rgba(0,175,255,.4),transparent);
    margin: 24px 0 12px;
}

.results-title {
    color: #eaf8ff;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 12px;
}

.results-title:before {
    content: "";
    display: inline-block;
    width: 36px;
    height: 3px;
    background: #00dfff;
    margin-right: 12px;
    vertical-align: middle;
    box-shadow: 0 0 12px #00cfff;
}

.stExpander {
    border: 1px solid rgba(0,164,242,.65) !important;
    border-radius: 13px !important;
    background: linear-gradient(145deg,rgba(3,39,86,.76),rgba(2,21,53,.85)) !important;
}

.stExpander details summary {
    color: #dff8ff !important;
}

.report-card, .critic-card {
    border: 1px solid rgba(0,184,255,.65);
    border-radius: 15px;
    background: linear-gradient(145deg,rgba(2,39,88,.78),rgba(2,20,54,.88));
    padding: 22px;
    margin-top: 10px;
    box-shadow: 0 12px 35px rgba(0,0,0,.22);
}

.report-label, .critic-label {
    color: #00e0ff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    padding-bottom: 9px;
    border-bottom: 2px solid rgba(0,218,255,.55);
    margin-bottom: 17px;
}

.critic-label {
    color: #49efd9;
    border-bottom-color: rgba(73,239,217,.5);
}

.stDownloadButton > button {
    width: auto !important;
    min-width: 240px;
    margin: 14px auto 0;
    display: block;
    border-radius: 10px !important;
    background: linear-gradient(100deg,#00dfee,#0094ff) !important;
    color: #001329 !important;
    font-weight: 700 !important;
}

.metric-card {
    padding: 14px;
    text-align: center;
    border: 1px solid rgba(0,160,240,.55);
    border-radius: 13px;
    background: rgba(3,30,71,.7);
}

.metric-value {
    color: #00dcff;
    font-size: 23px;
    font-weight: 700;
}

.metric-label {
    color: #719ac1;
    font-size: 10px;
    margin-top: 3px;
}

.running-message {
    margin-top: 10px;
    padding: 12px;
    text-align: center;
    border-radius: 12px;
    color: #9edfff;
    border: 1px solid rgba(0,193,255,.35);
    background: rgba(0,126,200,.08);
}

.footer {
    text-align: center;
    margin-top: 32px;
    color: #3489ba;
    font-size: 11px;
    letter-spacing: 1px;
}

@media (max-width: 900px) {
    .visual-pipeline {
        flex-wrap: wrap;
        gap: 8px;
    }
    .pipeline-node {
        min-width: 140px;
    }
    .pipeline-arrow {
        display: none;
    }
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# STATE
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = {}
if "running" not in st.session_state:
    st.session_state.running = False
if "done" not in st.session_state:
    st.session_state.done = False
if "elapsed" not in st.session_state:
    st.session_state.elapsed = 0

# ============================================================
# HELPERS
# ============================================================

def render_agent(icon, name, description, status):
    if status == "running":
        card_class = "agent-running"
        status_html = '<span class="agent-status status-running"><span class="loading-dot">●</span> RUNNING</span>'
    elif status == "done":
        card_class = "agent-done"
        status_html = '<span class="agent-status status-done">✓ DONE</span>'
    else:
        card_class = "agent-waiting"
        status_html = '<span class="agent-status status-waiting">WAITING</span>'

    st.markdown(
        f"""
        <div class="agent-card {card_class}">
            <div class="agent-icon">{icon}</div>
            <div>
                <div class="agent-name">{name}</div>
                <div class="agent-description">{description}</div>
            </div>
            {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def get_step_status(step, results, running):
    steps = ["search", "reader", "writer", "critic"]

    if step in results:
        return "done"

    if running:
        for current_step in steps:
            if current_step not in results:
                return "running" if current_step == step else "waiting"

    return "waiting"

def render_pipeline(results, running):
    render_agent("🔍", "Search Agent", "Finds recent and reliable information", get_step_status("search", results, running))
    render_agent("📄", "Reader Agent", "Scrapes and analyzes useful sources", get_step_status("reader", results, running))
    render_agent("✍️", "Writer Chain", "Creates the structured research report", get_step_status("writer", results, running))
    render_agent("🧠", "Critic Chain", "Reviews quality and gives a score", get_step_status("critic", results, running))

def progress_value(results):
    return sum(1 for key in ["search", "reader", "writer", "critic"] if key in results)

# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">MULTI-AGENT AI SYSTEM</div>
        <h1 class="hero-title">🧠 Research<span>Mind</span></h1>
        <div class="hero-subtitle">
            Four specialized AI agents collaborate — searching, scraping, writing,
            and critiquing — to deliver a polished research report on any topic.
        </div>
    </div>

    <div class="visual-pipeline">
        <div class="pipeline-node"><div class="pipeline-icon">🔍</div>SEARCH</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node"><div class="pipeline-icon">📄</div>Read</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node"><div class="pipeline-icon">✍️</div>Write</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node"><div class="pipeline-icon">🧠</div>Review</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# MAIN INPUT + PIPELINE
# ============================================================

left, right = st.columns([1.25, 1], gap="large")

with left:
    st.markdown(
        """
        <div class="ui-card">
            <div class="section-title">Research Topic</div>
        """,
        unsafe_allow_html=True,
    )

    topic = st.text_input(
        "Research topic",
        placeholder="e.g. Quantum computing breakthroughs in 2025",
        key="topic_input",
        label_visibility="collapsed",
    )

    run_button = st.button(
        "⚡  Run Research Pipeline",
        use_container_width=True,
    )

    st.markdown(
        """
        <span class="try-label">TRY →</span>
        <span class="chip">LLM agents 2025</span>
        <span class="chip">CRISPR gene editing</span>
        <span class="chip">Fusion energy progress</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown('<div class="ui-card"><div class="agent-heading">Pipeline</div>', unsafe_allow_html=True)
    render_pipeline(st.session_state.results, st.session_state.running)

    completed = progress_value(st.session_state.results)
    percentage = int((completed / 4) * 100)

    st.markdown(
        f"""
        <div class="progress-container">
            <div class="progress-label">
                <span>PIPELINE PROGRESS</span>
                <span>{percentage}%</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{percentage}%"></div>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# RUN RESEARCH PIPELINE


if run_button:
    if not topic.strip():
        st.warning("⚠️ Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.session_state.elapsed = 0
        st.session_state.topic = topic.strip()
        st.rerun()


# ============================================================
# EXECUTE FOUR AGENTS
# ============================================================

if st.session_state.running:

    topic_value = st.session_state.get("topic", "").strip()
    pipeline_start = time.perf_counter()
    current_stage = "Search Agent"

    try:
        with st.status(
            "🧠 ResearchMind is working...",
            expanded=True,
        ) as pipeline_status:



            # ----------------------------------------
            # SEARCH AGENT
            # ----------------------------------------
            search_start = time.time()

            search_agent = build_search_agent()

            search_response = search_agent.invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"""
Find recent, reliable and useful information about:

{topic_value}

IMPORTANT:
- Use the web_search tool.
- Preserve the actual URLs returned by the tool.
- Do not replace URLs with source names.
"""
                        )
                    ]
                }
            )

            # Extract the actual web_search tool output,
            # which contains the URLs.
            search_results = "\n\n".join(
                str(message.content)
                for message in search_response["messages"]
                if getattr(message, "type", "") == "tool"
                and getattr(message, "name", "") == "web_search"
                and message.content
            )

            # Fallback if no tool output was captured.
            if not search_results:
                search_results = search_response["messages"][-1].content

            st.session_state.results["search"] = search_results

            print(
                "[PERFORMANCE] Search Agent: "
                f"{time.perf_counter() - search_start:.2f} seconds"
            )

            # ------------------------------------------------
            # 2. READER AGENT
            # ------------------------------------------------

            current_stage = "Reader Agent"
            st.write("📖 Reader Agent is analyzing a source...")

            reader_start = time.perf_counter()

            reader_agent = build_reader_agent()

            reader_response = reader_agent.invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"""
Based on these search results about "{topic_value}",
choose the most relevant URL and extract useful information.

Search Results:

{search_results[:3000]}
"""
                        )
                    ]
                }
            )

            reader_content = reader_response["messages"][-1].content

            st.session_state.results["reader"] = reader_content

            print(
                "[PERFORMANCE] Reader Agent: "
                f"{time.perf_counter() - reader_start:.2f} seconds"
            )



            # ------------------------------------------------
            # 3. WRITER CHAIN
            # ------------------------------------------------

            current_stage = "Writer Chain"
            st.write("✍️ Writer is preparing the report...")

            writer_start = time.perf_counter()

            research_combined = f"""
ORIGINAL SEARCH RESULTS
Preserve the actual URLs exactly as provided.

{search_results}

DETAILED READER CONTENT

{reader_content}
"""

            report = writer_chain.invoke(
                {
                    "topic": topic_value,
                    "research": research_combined,
                }
            )

            st.session_state.results["writer"] = report

            print(
                "[PERFORMANCE] Writer Chain: "
                f"{time.perf_counter() - writer_start:.2f} seconds"
            )

                        

            # ------------------------------------------------
            # 4. CRITIC CHAIN
            # ------------------------------------------------

            current_stage = "Critic Chain"
            st.write("🧐 Critic is reviewing the report...")

            critic_start = time.perf_counter()

            feedback = critic_chain.invoke(
                {
                    "report": report,
                }
            )

            st.session_state.results["critic"] = feedback

            print(
                "[PERFORMANCE] Critic Chain: "
                f"{time.perf_counter() - critic_start:.2f} seconds"
            )

            # ------------------------------------------------
            # COMPLETE
            # ------------------------------------------------

            total_elapsed = time.perf_counter() - pipeline_start

            st.session_state.elapsed = total_elapsed
            st.session_state.running = False
            st.session_state.done = True

            pipeline_status.update(
                label="✅ Research completed successfully!",
                state="complete",
                expanded=False,
            )

            print(
                "[PERFORMANCE] Total pipeline: "
                f"{total_elapsed:.2f} seconds"
            )

    except Exception as error:
        st.session_state.running = False
        st.session_state.done = False

        error_message = (
            f"❌ {current_stage} failed.\n\n"
            f"{type(error).__name__}: {error}"
        )

        print(f"\n[ERROR] {error_message}")
        st.error(error_message)

    else:
        # Refresh only after successful completion.
        st.rerun()


# ============================================================
# DISPLAY RESULTS
# ============================================================

if st.session_state.done and st.session_state.results:
    results = st.session_state.results

    sources = extract_sources(results.get("search", ""))


    # -----------------------------------------------------
    # SOURCE CARDS
    # -----------------------------------------------------
    st.markdown("### 🔗 Research Sources")

    if sources:
        for start in range(0, len(sources), 2):
            columns = st.columns(2)

            for column, source in zip(
                columns, sources[start:start + 2]
            ):
                with column:
                    with st.container(border=True):
                        st.markdown(f"**{source['title']}**")

                        thumbnail = get_page_thumbnail(source["url"])

                        if thumbnail:
                            try:
                                st.image(
                                    thumbnail,
                                    use_container_width=True,
                                )
                            except Exception:
                                st.caption("Preview image unavailable.")
                        else:
                            st.caption("No preview image available.")

                        if source.get("snippet"):
                            st.write(source["snippet"])
                        else:
                            st.caption(source["url"])

                        st.markdown(
                            f"[🔗 Open source]({source['url']})"
                        )
    else:
        st.info(
            "No source URLs were detected in the search results. "
            "You can still view the existing research below."
        )

    # -----------------------------------------------------
    # EXISTING SEARCH AND READER RESULTS
    # -----------------------------------------------------
    st.markdown("### 🔍 Search Results")
    with st.expander("View search information"):
        st.write(results.get("search", ""))

    st.markdown("### 📄 Source Analysis")
    with st.expander("View reader analysis"):
        st.write(results.get("reader", ""))

    # -----------------------------------------------------
    # FINAL REPORT AND DOWNLOADS
    # -----------------------------------------------------
    st.markdown("### ✍️ Final Research Report")

    report = results.get("writer", "")
    st.markdown(report)

    st.download_button(
        label="⬇️ Download Research Report (.txt)",
        data=report,
        file_name="research_report.txt",
        mime="text/plain",
        use_container_width=True,
    )

    pdf_data = create_pdf_report(
        st.session_state.get("topic", ""),
        report,
        sources,
    )

    st.download_button(
        label="📄 Download Research Report (.pdf)",
        data=pdf_data,
        file_name="research_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# -----------------------------------------------------
# CRITIC REVIEW
# -----------------------------------------------------

critic_feedback = st.session_state.results.get("critic", "")

critic_feedback = "\n".join(
    line
    for line in critic_feedback.splitlines()
    if not line.strip().startswith("Score:")
)

st.markdown("### 🧠 Critic Review")
st.markdown(critic_feedback)

st.markdown(
    '<div class="footer">'
    'ResearchMind • Multi-Agent AI Research System'
    '</div>',
    unsafe_allow_html=True,
)



