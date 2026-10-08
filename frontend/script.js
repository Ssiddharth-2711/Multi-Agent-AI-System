
const BACKEND_URL = "http://127.0.0.1:8000";


// ==================================================
// DOM ELEMENTS
// ==================================================

const topicInput = document.getElementById("topicInput");
const researchBtn = document.getElementById("researchBtn");


// ==================================================
// START RESEARCH
// ==================================================

researchBtn.addEventListener("click", startResearch);


// Also allow ENTER key
topicInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        startResearch();
    }
});


// ==================================================
// MAIN FUNCTION
// ==================================================

async function startResearch() {

    const topic = topicInput.value.trim();

    if (!topic) {
        alert("Please enter a research topic.");
        return;
    }


    // Disable button
    researchBtn.disabled = true;

    // Reset UI
    resetUI();

    // Show initial status
    updateAgent("search", "working", "Starting web search...");


    try {

        const response = await fetch(
            `${BACKEND_URL}/research/stream`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },

                body: JSON.stringify({
                    topic: topic
                })
            }
        );


        if (!response.ok) {
            throw new Error(
                `Backend returned ${response.status}`
            );
        }


        if (!response.body) {
            throw new Error("Streaming is not supported by this browser.");
        }


        // ==================================================
        // READ SSE STREAM
        // ==================================================

        const reader = response.body.getReader();

        const decoder = new TextDecoder("utf-8");

        let buffer = "";


        while (true) {

            const { value, done } = await reader.read();

            if (done) {
                break;
            }


            buffer += decoder.decode(value, {
                stream: true
            });


            // SSE messages are separated by blank lines
            const events = buffer.split("\n\n");

            buffer = events.pop();


            for (const event of events) {

                if (!event.trim()) {
                    continue;
                }


                const dataLine = event
                    .split("\n")
                    .find(line => line.startsWith("data:"));


                if (!dataLine) {
                    continue;
                }


                const jsonText = dataLine
                    .replace(/^data:\s*/, "");


                try {

                    const message = JSON.parse(jsonText);

                    handleServerEvent(message);

                } catch (error) {

                    console.error(
                        "Could not parse SSE message:",
                        error,
                        jsonText
                    );
                }
            }
        }


    } catch (error) {

        console.error("Research error:", error);

        showError(
            "Backend connection failed. Make sure FastAPI is running."
        );

    } finally {

        researchBtn.disabled = false;
    }
}


// ==================================================
// HANDLE SERVER EVENTS
// ==================================================

function handleServerEvent(message) {

    const type = message.type;
    const data = message.data;


    // ----------------------------------------------
    // START
    // ----------------------------------------------

    if (type === "start") {

        updateStatus(
            "Research started..."
        );

        return;
    }


    // ----------------------------------------------
    // PROGRESS
    // ----------------------------------------------

    if (type === "progress") {

        const agent = data.agent;
        const status = data.status;
        const messageText = data.message;


        updateAgent(
            agent,
            status,
            messageText
        );


        updateStatus(messageText);


        // Optional: show search result
        if (
            agent === "search" &&
            status === "complete" &&
            data.result
        ) {

            console.log(
                "Search Results:",
                data.result
            );
        }


        return;
    }


    // ----------------------------------------------
    // COMPLETE
    // ----------------------------------------------

    if (type === "complete") {

        updateStatus(
            "Research completed successfully 🎉"
        );


        displayFinalResult(data);

        return;
    }


    // ----------------------------------------------
    // ERROR
    // ----------------------------------------------

    if (type === "error") {

        showError(
            data.message || "Something went wrong."
        );

        return;
    }
}


// ==================================================
// UPDATE AGENT UI
// ==================================================

function updateAgent(agent, status, message) {

    /*
        IMPORTANT:

        These selectors support common IDs/classes.
        If your existing HTML uses different names,
        we can adjust them after testing.
    */

    const possibleSelectors = {
        search: [
            "#searchAgent",
            "#search-agent",
            ".search-agent"
        ],

        reader: [
            "#readerAgent",
            "#reader-agent",
            ".reader-agent"
        ],

        writer: [
            "#writerAgent",
            "#writer-agent",
            ".writer-agent"
        ],

        critic: [
            "#criticAgent",
            "#critic-agent",
            ".critic-agent"
        ]
    };


    const selectors = possibleSelectors[agent] || [];


    let element = null;


    for (const selector of selectors) {

        element = document.querySelector(selector);

        if (element) {
            break;
        }
    }


    if (element) {

        element.classList.remove(
            "working",
            "complete",
            "waiting",
            "active"
        );


        element.classList.add(status);


        const statusElement =
            element.querySelector(
                ".agent-status, .status, .agent-message"
            );


        if (statusElement) {
            statusElement.textContent = message;
        }
    }


    console.log(
        `[${agent}] ${status}: ${message}`
    );
}


// ==================================================
// STATUS MESSAGE
// ==================================================

function updateStatus(message) {

    const selectors = [
        "#statusMessage",
        "#status-message",
        ".status-message",
        "#liveMessage",
        ".live-message"
    ];


    for (const selector of selectors) {

        const element =
            document.querySelector(selector);


        if (element) {

            element.textContent = message;

            return;
        }
    }


    console.log(message);
}


// ==================================================
// DISPLAY FINAL RESULT
// ==================================================

function displayFinalResult(data) {

    const report =
        document.querySelector(
            "#report, #reportContent, .report-content"
        );


    if (report) {

        report.innerHTML = formatReport(
            data.report || "No report generated."
        );
    }


    const feedback =
        document.querySelector(
            "#feedback, #criticFeedback, .critic-feedback"
        );


    if (feedback) {

        feedback.innerHTML = formatReport(
            data.feedback || "No critic feedback."
        );
    }


    // Mark all agents complete
    updateAgent(
        "search",
        "complete",
        "Search completed ✓"
    );

    updateAgent(
        "reader",
        "complete",
        "Reading completed ✓"
    );

    updateAgent(
        "writer",
        "complete",
        "Report completed ✓"
    );

    updateAgent(
        "critic",
        "complete",
        "Review completed ✓"
    );


    // Show result section
    const resultSection =
        document.querySelector(
            "#resultSection, .result-section, #results"
        );


    if (resultSection) {

        resultSection.style.display = "block";

        resultSection.scrollIntoView({
            behavior: "smooth"
        });
    }


    // Make download button work
    setupDownload(data.report || "");
}


// ==================================================
// FORMAT REPORT
// ==================================================

function formatReport(text) {

    if (!text) {
        return "";
    }


    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
}


// ==================================================
// ERROR
// ==================================================

function showError(message) {

    updateStatus("❌ " + message);

    alert(message);
}


// ==================================================
// RESET UI
// ==================================================

function resetUI() {

    const resultSections = document.querySelectorAll(
        "#resultSection, .result-section, #results"
    );


    resultSections.forEach(section => {
        section.style.display = "none";
    });


    const agents = [
        "search",
        "reader",
        "writer",
        "critic"
    ];


    agents.forEach(agent => {

        updateAgent(
            agent,
            "waiting",
            "Waiting..."
        );
    });


    const report =
        document.querySelector(
            "#report, #reportContent, .report-content"
        );


    if (report) {
        report.innerHTML = "";
    }


    const feedback =
        document.querySelector(
            "#feedback, #criticFeedback, .critic-feedback"
        );


    if (feedback) {
        feedback.innerHTML = "";
    }
}


// ==================================================
// DOWNLOAD REPORT
// ==================================================

function setupDownload(reportText) {

    const downloadButton =
        document.querySelector(
            "#downloadBtn, .download-btn"
        );


    if (!downloadButton) {
        return;
    }


    downloadButton.onclick = () => {

        const blob = new Blob(
            [reportText],
            {
                type: "text/plain"
            }
        );


        const url =
            URL.createObjectURL(blob);


        const link =
            document.createElement("a");


        link.href = url;

        link.download =
            "AI_Research_Report.txt";


        document.body.appendChild(link);

        link.click();

        link.remove();


        URL.revokeObjectURL(url);
    };
}

