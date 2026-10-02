const contractFile = document.getElementById("contractFile");
const fileName = document.getElementById("fileName");
const analyzeButton = document.getElementById("analyzeButton");

const loading = document.getElementById("loading");
const errorMessage = document.getElementById("errorMessage");
const results = document.getElementById("results");

const analyzedFile = document.getElementById("analyzedFile");

const riskScore = document.getElementById("riskScore");
const riskLevel = document.getElementById("riskLevel");
const clauseCount = document.getElementById("clauseCount");
const uniqueClauseCount = document.getElementById("uniqueClauseCount");

const riskFactors = document.getElementById("riskFactors");
const detectedClauses = document.getElementById("detectedClauses");

const downloadButton = document.getElementById("downloadButton");


/* -------------------------------------------------------
   Semantic Search Elements
------------------------------------------------------- */

const searchQuery = document.getElementById("searchQuery");
const searchTopK = document.getElementById("searchTopK");
const searchButton = document.getElementById("searchButton");

const searchLoading = document.getElementById("searchLoading");
const searchError = document.getElementById("searchError");
const searchResults = document.getElementById("searchResults");


/* -------------------------------------------------------
   File Selection
------------------------------------------------------- */

contractFile.addEventListener("change", () => {

    const file = contractFile.files[0];

    if (!file) {
        fileName.textContent = "No file selected";
        analyzeButton.disabled = true;
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        fileName.textContent = "Please select a PDF file.";
        analyzeButton.disabled = true;
        return;
    }

    fileName.textContent = file.name;
    analyzeButton.disabled = false;

    hideError();
});


/* -------------------------------------------------------
   Analyze Contract
------------------------------------------------------- */

analyzeButton.addEventListener("click", async () => {

    const file = contractFile.files[0];

    if (!file) {
        showError("Please select a PDF contract first.");
        return;
    }

    const formData = new FormData();

    formData.append("file", file);

    setLoading(true);
    hideError();

    try {

        const response = await fetch("/analyze-contract", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {

            let message = "Contract analysis failed.";

            if (data.detail) {

                if (typeof data.detail === "string") {
                    message = data.detail;
                } else if (data.detail.error) {
                    message = data.detail.error;
                }
            }

            throw new Error(message);
        }

        displayResults(data);

    } catch (error) {

        console.error("Analysis error:", error);

        showError(
            error.message ||
            "Something went wrong while analyzing the contract."
        );

    } finally {

        setLoading(false);
    }
});


/* -------------------------------------------------------
   Display Results
------------------------------------------------------- */

function displayResults(data) {

    if (!data || !data.report) {
        showError("The API returned an invalid analysis report.");
        return;
    }

    const report = data.report;

    const summary = report.analysis_summary || {};
    const assessment = report.risk_assessment || {};

    /* File */

    analyzedFile.textContent =
        `Analyzed contract: ${data.filename || "Unknown file"}`;


    /* Summary */

    riskScore.textContent =
        assessment.risk_score ?? "--";

    riskLevel.textContent =
        assessment.risk_level ?? "--";

    clauseCount.textContent =
        summary.clause_detections ?? "--";

    uniqueClauseCount.textContent =
        summary.unique_clause_types ?? "--";


    /* Risk Level Styling */

    riskLevel.className = "";

    const level =
        String(assessment.risk_level || "")
        .toLowerCase();

    if (level === "high") {
        riskLevel.style.color = "#ef4444";
    } else if (level === "medium") {
        riskLevel.style.color = "#f59e0b";
    } else if (level === "low") {
        riskLevel.style.color = "#22c55e";
    }


    /* Risk Factors */

    renderRiskFactors(
        assessment.risk_analysis ||
        report.risk_analysis ||
        []
    );


    /* Detected Clauses */

    renderDetectedClauses(
        report.detected_clauses ||
        []
    );


    /* Show Results */

    results.classList.remove("hidden");

    results.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


/* -------------------------------------------------------
   Risk Factors
------------------------------------------------------- */

function renderRiskFactors(items) {

    riskFactors.innerHTML = "";

    if (!Array.isArray(items) || items.length === 0) {

        riskFactors.innerHTML = `
            <div class="risk-item">
                <div class="risk-reason">
                    No specific risk factors were returned.
                </div>
            </div>
        `;

        return;
    }


    items.forEach((item) => {

        const title =
            item.clause_type ||
            item.type ||
            item.name ||
            "Risk Factor";

        const points =
            item.points ??
            item.score ??
            0;

        const reason =
            item.reason ||
            item.description ||
            "Risk identified from the detected contract clause.";

        const matchedText =
            item.matched_text ||
            item.text ||
            "";


        const riskElement =
            document.createElement("div");

        riskElement.className = "risk-item";

        riskElement.innerHTML = `
            <div class="risk-item-header">
                <span class="risk-item-title">
                    ${escapeHtml(title)}
                </span>

                <span class="risk-points">
                    +${escapeHtml(String(points))} points
                </span>
            </div>

            <div class="risk-reason">
                ${escapeHtml(reason)}
            </div>

            ${
                matchedText
                    ? `
                    <div class="matched-text">
                        ${escapeHtml(matchedText)}
                    </div>
                    `
                    : ""
            }
        `;

        riskFactors.appendChild(riskElement);
    });
}


/* -------------------------------------------------------
   Detected Clauses
------------------------------------------------------- */

function renderDetectedClauses(clauses) {

    detectedClauses.innerHTML = "";

    if (!Array.isArray(clauses) || clauses.length === 0) {

        detectedClauses.innerHTML = `
            <div class="clause-card">
                <div class="clause-meta">
                    No clauses detected.
                </div>
            </div>
        `;

        return;
    }


    clauses.forEach((clause) => {

        const clauseType =
            clause.clause_type ||
            clause.type ||
            clause.label ||
            "Unknown Clause";

        const section =
            clause.section_title ||
            clause.section ||
            "Contract Section";

        const matchedText =
            clause.matched_text ||
            clause.text ||
            "";


        const clauseElement =
            document.createElement("div");

        clauseElement.className = "clause-card";

        clauseElement.innerHTML = `
            <div class="clause-title">
                ${escapeHtml(clauseType)}
            </div>

            <div class="clause-meta">
                Section:
                ${escapeHtml(section)}
            </div>

            ${
                matchedText
                    ? `
                    <div class="matched-text">
                        ${escapeHtml(matchedText)}
                    </div>
                    `
                    : ""
            }
        `;

        detectedClauses.appendChild(clauseElement);
    });
}


/* -------------------------------------------------------
   Semantic Contract Search
------------------------------------------------------- */

if (searchButton) {

    searchButton.addEventListener("click", performSemanticSearch);
}


if (searchQuery) {

    searchQuery.addEventListener("keydown", (event) => {

        if (event.key === "Enter") {
            performSemanticSearch();
        }
    });
}


/* -------------------------------------------------------
   Perform Semantic Search
------------------------------------------------------- */

async function performSemanticSearch() {

    if (!searchQuery || !searchButton) {
        return;
    }

    const query = searchQuery.value.trim();

    if (!query) {
        showSearchError(
            "Please enter a question or search query."
        );
        return;
    }

    if (query.length < 2) {
        showSearchError(
            "Search query must contain at least 2 characters."
        );
        return;
    }

    const topK = Number(searchTopK?.value || 5);

    setSearchLoading(true);
    hideSearchError();

    searchResults.innerHTML = "";

    try {

        const response = await fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: query,
                top_k: topK
            })
        });

        const data = await response.json();

        if (!response.ok) {

            let message = "Semantic search failed.";

            if (data.detail) {

                if (typeof data.detail === "string") {
                    message = data.detail;
                } else if (data.detail.error) {
                    message = data.detail.error;
                }
            }

            throw new Error(message);
        }

        renderSearchResults(data);

    } catch (error) {

        console.error("Semantic search error:", error);

        showSearchError(
            error.message ||
            "Something went wrong while searching the contract."
        );

    } finally {

        setSearchLoading(false);
    }
}


/* -------------------------------------------------------
   Render Semantic Search Results
------------------------------------------------------- */

function renderSearchResults(data) {

    searchResults.innerHTML = "";

    if (
        !data ||
        !Array.isArray(data.results) ||
        data.results.length === 0
    ) {

        searchResults.innerHTML = `
            <div class="search-empty">
                No relevant contract sections were found.
            </div>
        `;

        return;
    }


    const heading = document.createElement("div");

    heading.className = "search-result-summary";

    heading.textContent =
        `Found ${data.results.length} relevant section${
            data.results.length === 1 ? "" : "s"
        }`;

    searchResults.appendChild(heading);


    data.results.forEach((result, index) => {

        const resultElement =
            document.createElement("div");

        resultElement.className =
            "search-result-card";


        const rank =
            index + 1;

        const score =
            Number(result.score ?? 0);


        const scoreText =
            score.toFixed(4);


        const section =
            result.section_title ||
            result.section ||
            result.title ||
            "Contract Section";


        const text =
            result.text ||
            result.content ||
            result.section_text ||
            "";


        resultElement.innerHTML = `
            <div class="search-result-header">

                <div class="search-result-rank">
                    #${rank}
                </div>

                <div class="search-result-title">
                    ${escapeHtml(section)}
                </div>

                <div class="search-result-score">
                    ${escapeHtml(scoreText)}
                </div>

            </div>

            ${
                text
                    ? `
                    <div class="search-result-text">
                        ${escapeHtml(text)}
                    </div>
                    `
                    : ""
            }
        `;


        searchResults.appendChild(resultElement);
    });


    searchResults.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}


/* -------------------------------------------------------
   Search Loading State
------------------------------------------------------- */

function setSearchLoading(isLoading) {

    if (!searchLoading || !searchButton) {
        return;
    }

    if (isLoading) {

        searchLoading.classList.remove("hidden");

        searchButton.disabled = true;

        searchButton.textContent =
            "Searching...";

    } else {

        searchLoading.classList.add("hidden");

        searchButton.disabled = false;

        searchButton.textContent =
            "Search";
    }
}


/* -------------------------------------------------------
   Search Error Handling
------------------------------------------------------- */

function showSearchError(message) {

    if (!searchError) {
        return;
    }

    searchError.textContent =
        message;

    searchError.classList.remove("hidden");
}


function hideSearchError() {

    if (!searchError) {
        return;
    }

    searchError.textContent =
        "";

    searchError.classList.add("hidden");
}


/* -------------------------------------------------------
   Loading State
------------------------------------------------------- */

function setLoading(isLoading) {

    if (isLoading) {

        loading.classList.remove("hidden");

        analyzeButton.disabled = true;

        analyzeButton.textContent =
            "Analyzing...";

    } else {

        loading.classList.add("hidden");

        analyzeButton.disabled =
            !contractFile.files.length;

        analyzeButton.textContent =
            "Analyze Contract";
    }
}


/* -------------------------------------------------------
   Error Handling
------------------------------------------------------- */

function showError(message) {

    errorMessage.textContent = message;

    errorMessage.classList.remove("hidden");
}


function hideError() {

    errorMessage.textContent = "";

    errorMessage.classList.add("hidden");
}


/* -------------------------------------------------------
   Download Report
------------------------------------------------------- */

downloadButton.addEventListener("click", () => {

    window.open(
        "/download-report",
        "_blank"
    );
});


/* -------------------------------------------------------
   HTML Safety
------------------------------------------------------- */

function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}