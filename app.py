
import streamlit as st
import time
from agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)

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


if run_button:
    if not topic.strip():
        st.warning("⚠️ Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.session_state.elapsed = 0
        st.rerun()



if st.session_state.running and not st.session_state.done:
    start_time = time.time()
    topic_value = st.session_state.topic_input.strip()
    results = {}

    search_status = st.empty()

    with search_status:
        st.info("🔍 Search Agent is searching the web...")

    try:
        search_agent = build_search_agent()
        search_response = search_agent.invoke({
            "messages": [
                (
                    "user",
                    f"Find recent, reliable and detailed information about: {topic_value}",
                )
            ]
        })
        results["search"] = search_response["messages"][-1].content
        st.session_state.results = dict(results)

    except Exception as e:
        st.session_state.running = False
        st.error(f"❌ Search Agent failed:\n\n{e}")
        st.stop()

    with search_status:
        st.info("📄 Reader Agent is analyzing the best sources...")

    try:
        reader_agent = build_reader_agent()
        reader_response = reader_agent.invoke({
            "messages": [
                (
                    "user",
                    (
                        f"Based on the following search results about '{topic_value}', "
                        "pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{results['search'][:800]}"
                    ),
                )
            ]
        })
        results["reader"] = reader_response["messages"][-1].content
        st.session_state.results = dict(results)

    except Exception as e:
        st.session_state.running = False
        st.error(f"❌ Reader Agent failed:\n\n{e}")
        st.stop()

    with search_status:
        st.info("✍️ Writer Agent is creating your research report...")

    try:
        combined_research = (
            "SEARCH RESULTS:\n"
            f"{results['search']}\n\n"
            "DETAILED SCRAPED CONTENT:\n"
            f"{results['reader']}"
        )

        results["writer"] = writer_chain.invoke({
            "topic": topic_value,
            "research": combined_research,
        })

        st.session_state.results = dict(results)

    except Exception as e:
        st.session_state.running = False
        st.error(f"❌ Writer Agent failed:\n\n{e}")
        st.stop()

    with search_status:
        st.info("🧠 Critic Agent is reviewing the report...")

    try:
        results["critic"] = critic_chain.invoke({
            "report": results["writer"]
        })
        st.session_state.results = dict(results)

    except Exception as e:
        st.session_state.running = False
        st.error(f"❌ Critic Agent failed:\n\n{e}")
        st.stop()

    st.session_state.elapsed = time.time() - start_time
    st.session_state.running = False
    st.session_state.done = True
    st.rerun()



results = st.session_state.results

if results:
    st.markdown('<div class="results-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="results-title">RESULTS</div>', unsafe_allow_html=True)

    # Metrics retained from original app
    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.markdown(
            '<div class="metric-card"><div class="metric-value">4</div><div class="metric-label">AI AGENTS</div></div>',
            unsafe_allow_html=True,
        )

    with metric2:
        st.markdown(
            '<div class="metric-card"><div class="metric-value">100%</div><div class="metric-label">PIPELINE COMPLETE</div></div>',
            unsafe_allow_html=True,
        )

    with metric3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{st.session_state.elapsed:.1f}s</div><div class="metric-label">RESEARCH TIME</div></div>',
            unsafe_allow_html=True,
        )

    result_left, result_middle, result_right = st.columns([1, 1.35, 1], gap="large")

    with result_left:
        if "search" in results:
            with st.expander("🔍  Search Results (raw)", expanded=False):
                st.markdown(results["search"])

        if "reader" in results:
            with st.expander("📄  Scraped Content (raw)", expanded=False):
                st.markdown(results["reader"])

    with result_middle:
        if "writer" in results:
            st.markdown(
                """
                <div class="report-card">
                    <div class="report-label">📄 Final Research Report</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(results["writer"])
            st.markdown("</div>", unsafe_allow_html=True)

            st.download_button(
                label="⬇️  Download Report (.md)",
                data=results["writer"],
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown",
            )

    with result_right:
        if "critic" in results:
            st.markdown(
                """
                <div class="critic-card">
                    <div class="critic-label">🧠 Critic Feedback</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(results["critic"])
            st.markdown("</div>", unsafe_allow_html=True)


st.markdown(
    """
    <div class="footer">
        ─────────────── &nbsp;&nbsp; ResearchMind &nbsp;&nbsp; ───────────────
    </div>
    """,
    unsafe_allow_html=True,
)

