// ─────────────────────────────────────────────────────────────────
//  Fake Job Detector — Universal Content Script
//  Works on: LinkedIn, Indeed, Naukri, Glassdoor, Internshala,
//            Wellfound, Shine, Monster, Instahyre, Cutshort,
//            company career pages, and any generic job posting page.
// ─────────────────────────────────────────────────────────────────

let hasRun = false;

// ── Site-specific extraction map ─────────────────────────────────
const SITE_RULES = [
    {
        match: "linkedin.com/jobs",
        title:   [".job-details-jobs-unified-top-card__job-title h1", ".jobs-unified-top-card__job-title h1", "h1"],
        company: [".job-details-jobs-unified-top-card__company-name a", ".jobs-unified-top-card__company-name", ".ember-view.t-black.t-normal"],
        desc:    [".jobs-description-content__text", ".jobs-description__content", ".job-view-layout"]
    },
    {
        match: "indeed.com",
        title:   ["[data-testid='jobsearch-JobInfoHeader-title'] span", ".jobsearch-JobInfoHeader-title", "h1"],
        company: ["[data-testid='inlineHeader-companyName'] a", ".jobsearch-CompanyInfoWithoutHeaderImage a", ".jobsearch-InlineCompanyRating-companyHeader a"],
        desc:    ["#jobDescriptionText", ".jobsearch-jobDescriptionText", "[data-testid='jobDescription']"]
    },
    {
        match: "naukri.com",
        title:   [".jd-header-title", "h1.styles_jd-header-title__rZwM1", "h1"],
        company: [".jd-header-comp-name a", ".comp-name", ".styles_comp-name__Y8Bxf a"],
        desc:    [".job-desc", ".styles_JDC__dang-inner-html__h0K4t", "#job-description"]
    },
    {
        match: "glassdoor.com",
        title:   ["[data-test='job-title']", ".JobDetails_jobTitle__Rw_gn", "h1"],
        company: ["[data-test='employer-name']", ".JobDetails_companyName__t7P9J", ".EmployerProfile_profileContainer__X5ib9 a"],
        desc:    ["[data-test='description']", ".JobDetails_jobDescription__uW_fK", ".JobDetails_jobDescription__6VEB_"]
    },
    {
        match: "internshala.com",
        title:   [".profile h1", ".job_title h1", "h1"],
        company: [".company-name a", ".company_name a", ".internship_heading .company-name"],
        desc:    [".internship_details .text-container", ".about_company_text_container", ".requirements div"]
    },
    {
        match: "wellfound.com",
        title:   ["h1[class*='title']", ".styles_title__xpQDw", "h1"],
        company: ["[class*='startup-link']", "a[class*='company']", ".styles_companyLink__DliQ8"],
        desc:    ["[class*='description']", ".styles_description__", ".prose"]
    },
    {
        match: "shine.com",
        title:   [".jd-header h1", ".job-title", "h1"],
        company: [".jd-header .company-name", ".company-name a"],
        desc:    [".jd-desc", ".job-desc-con", "#jd-desc"]
    },
    {
        match: "monster.com",
        title:   ["h1.title", "[itemprop='title']", "h1"],
        company: ["[itemprop='hiringOrganization'] [itemprop='name']", ".company-name"],
        desc:    ["#job-description", ".job-description", "[itemprop='description']"]
    },
    {
        match: "instahyre.com",
        title:   [".job-title h1", "h1"],
        company: [".company-name", "a.company-link"],
        desc:    [".job-description", ".jd-content"]
    },
    {
        match: "cutshort.io",
        title:   ["h1[class*='title']", "h1"],
        company: ["[class*='companyName']", "a[href*='/company/']"],
        desc:    ["[class*='description']", ".job-description"]
    },
    {
        match: "foundit.in",
        title:   ["h1.job-tittle", ".job-title", "h1"],
        company: [".company-name a", ".org-name"],
        desc:    ["#jdDiv", ".job-description"]
    },
    {
        match: "timesjobs.com",
        title:   ["h1.heading-trun", "h1"],
        company: [".joblist-comp-name a", ".search-li .c-name"],
        desc:    [".jd-desc", ".job-description-main", ".jd-job-description-main"]
    },
    {
        match: "freshersworld.com",
        title:   [".job-head h1", "h1"],
        company: [".company-name", ".comp-name"],
        desc:    [".job-desc-detail", ".description"]
    },
    {
        match: "hirist.tech",
        title:   ["h1", ".jobtitle"],
        company: [".company-name", ".org-name"],
        desc:    [".job-description", ".desc-content"]
    },
];

// ── Generic fallback selectors (for company career pages & unknowns) ──
const GENERIC_TITLE_SELECTORS = [
    "h1[class*='job']", "h1[class*='title']", "h1[class*='position']",
    "[class*='job-title']", "[class*='jobtitle']", "[class*='position-title']",
    "[itemprop='title']", "h1"
];

const GENERIC_COMPANY_SELECTORS = [
    "[class*='company-name']", "[class*='companyName']", "[class*='employer']",
    "[class*='org-name']", "[itemprop='hiringOrganization'] [itemprop='name']",
    "[class*='brand']", "[class*='recruiter']",
    "meta[property='og:site_name']",    // og meta tag
    "meta[name='author']"               // author meta tag
];

const GENERIC_DESC_SELECTORS = [
    "[class*='job-description']", "[class*='jobDescription']", "[class*='job_description']",
    "[id*='job-description']",   "[id*='jobDescription']",    "[id*='job_description']",
    "[class*='job-details']",    "[class*='jobDetails']",
    "[class*='description']",    "[class*='jd-content']",
    "[class*='posting-content']","[class*='vacancy-desc']",
    "[itemprop='description']",  "article", "main"
];

// ── Keyword heuristic: does this page look like a job posting? ──
const JOB_KEYWORDS = [
    "responsibilities", "requirements", "qualifications", "we are looking",
    "job description", "about the role", "what you'll do", "apply now",
    "experience required", "skills required", "ctc", "salary", "lpa",
    "internship", "full-time", "part-time", "remote", "hybrid", "on-site",
    "years of experience", "bachelor", "master", "degree", "b.tech", "mba"
];

function isJobPage(text) {
    const lower = text.toLowerCase();
    const hits = JOB_KEYWORDS.filter(k => lower.includes(k)).length;
    return hits >= 3;
}

// ── Query helper: first matching selector ──
function queryFirst(selectors) {
    for (const sel of selectors) {
        try {
            // Handle meta tags
            if (sel.startsWith("meta")) {
                const el = document.querySelector(sel);
                if (el) return el.getAttribute("content") || null;
            }
            const el = document.querySelector(sel);
            if (el && el.innerText && el.innerText.trim().length > 1) {
                return el.innerText.trim();
            }
        } catch (_) {}
    }
    return null;
}

// ── Extract company name from page URL as last resort ──
function companyFromUrl() {
    const url = window.location.hostname;
    // Remove common subdomains and TLDs
    const parts = url.replace(/^www\./, "").split(".");
    if (parts.length >= 2) {
        const candidate = parts[0];
        // Skip generic platforms
        const skip = ["careers", "jobs", "apply", "hire", "recruit", "work"];
        if (!skip.includes(candidate.toLowerCase())) {
            return candidate.charAt(0).toUpperCase() + candidate.slice(1);
        }
        // careers.companyname.com → companyname
        if (parts.length >= 3) {
            return parts[1].charAt(0).toUpperCase() + parts[1].slice(1);
        }
    }
    return null;
}

// ── Main extraction function ──
function extractJobData() {
    const href = window.location.href;
    const hostname = window.location.hostname.toLowerCase();

    // Find matching site rule
    const rule = SITE_RULES.find(r => href.includes(r.match) || hostname.includes(r.match));

    let jobTitle   = rule ? queryFirst(rule.title)   : null;
    let companyName = rule ? queryFirst(rule.company) : null;
    let descText    = null;

    // Try site-specific desc selector
    if (rule) {
        for (const sel of rule.desc) {
            const el = document.querySelector(sel);
            if (el && el.innerText && el.innerText.trim().length > 80) {
                descText = el.innerText.trim();
                break;
            }
        }
    }

    // Fallback: generic selectors
    if (!jobTitle)    jobTitle    = queryFirst(GENERIC_TITLE_SELECTORS);
    if (!companyName) companyName = queryFirst(GENERIC_COMPANY_SELECTORS);
    if (!descText) {
        for (const sel of GENERIC_DESC_SELECTORS) {
            try {
                const el = document.querySelector(sel);
                if (el && el.innerText && el.innerText.trim().length > 150) {
                    descText = el.innerText.trim();
                    break;
                }
            } catch (_) {}
        }
    }

    // Last resort for company: extract from URL
    if (!companyName || companyName === "Unknown Company") {
        companyName = companyFromUrl() || "Unknown Company";
    }

    // Last resort for description: page body if it looks like a job page
    if (!descText) {
        const bodyText = document.body.innerText;
        if (isJobPage(bodyText)) {
            descText = bodyText.substring(0, 5000);
        }
    }

    // Final fallbacks
    jobTitle    = jobTitle    || document.title || "Unknown Title";
    companyName = companyName || "Unknown Company";

    return { jobTitle, companyName, descText };
}

// ── Main entry ──
function extractAndAnalyze() {
    if (hasRun) return;

    const { jobTitle, companyName, descText } = extractJobData();

    // Skip if no meaningful description found
    if (!descText || descText.trim().length < 80) return;

    hasRun = true;

    const description = descText.length > 5000 ? descText.substring(0, 5000) : descText;

    // Send to backend via background worker (bypasses CSP)
    chrome.runtime.sendMessage({
        action: "api_analyze",
        payload: { company_name: companyName, job_title: jobTitle, description }
    }, (response) => {
        if (!response) {
            console.error("Fake Job Detector: Extension context invalidated.");
            return;
        }
        if (!response.success) {
            console.error("Fake Job Detector: Backend unreachable. Make sure python app.py is running.", response.error);
            return;
        }

        const data = response.data;
        showFloatingAlert(data);

        // Highlight suspicious words in the description element
        let wordsToHighlight = [];
        if (data.highlight_words && data.highlight_words.length > 0) {
            wordsToHighlight = data.highlight_words;
        } else if (data.source === "memory" && data.reasons && data.reasons.length > 0) {
            data.reasons.forEach(r => {
                const match = r.match(/'([^']+)'/);
                if (match) wordsToHighlight.push(match[1]);
            });
        }

        if (wordsToHighlight.length > 0) {
            // Find the desc element again (avoid highlighting full body)
            const { descEl } = extractDescElement();
            if (descEl && descEl !== document.body) {
                highlightWordsInElement(descEl, wordsToHighlight);
            }
        }
    });
}

// Returns the description DOM element (for highlighting)
function extractDescElement() {
    const href = window.location.href;
    const rule = SITE_RULES.find(r => href.includes(r.match));
    if (rule) {
        for (const sel of rule.desc) {
            const el = document.querySelector(sel);
            if (el) return { descEl: el };
        }
    }
    for (const sel of GENERIC_DESC_SELECTORS) {
        try {
            const el = document.querySelector(sel);
            if (el && el.innerText && el.innerText.trim().length > 80) return { descEl: el };
        } catch (_) {}
    }
    return { descEl: null };
}

function highlightWordsInElement(element, words) {
    let html = element.innerHTML;
    words.forEach(word => {
        const regex = new RegExp(`\\b${word}\\b`, "gi");
        html = html.replace(regex, `<span style="background-color:#ffcccc;color:#cc0000;font-weight:bold;padding:0 2px;border-radius:2px;">$&</span>`);
    });
    element.innerHTML = html;
}

function showFloatingAlert(data) {
    const isFake = data.label === "Fake";
    const isMemory = data.source === "memory";

    const bgColor   = isFake ? (isMemory ? "#8b0000" : "#e74c3c") : "#2ecc71";
    const titleText = isFake ? "⚠️ Suspicious Job Detected" : "✅ Looks Legitimate";

    let sourceText = "AI Engine";
    if (data.source === "memory")      sourceText = "Memory (Reported)";
    else if (data.source === "hybrid_ai") sourceText = "Hybrid AI (ML+NLP+LLM)";
    else if (data.source === "llm")    sourceText = "AI (LLM)";
    else                               sourceText = "AI (Keyword)";

    const alertDiv = document.createElement("div");
    alertDiv.id = "fake-job-alert";
    alertDiv.style.cssText = `
        position:fixed; top:20px; right:20px;
        background-color:${bgColor}; color:white;
        padding:20px; border-radius:10px;
        box-shadow:0 6px 15px rgba(0,0,0,0.4);
        z-index:2147483647; font-family:Arial,sans-serif;
        min-width:300px; border:1px solid rgba(255,255,255,0.2);
        transition: opacity 0.3s;
    `;

    alertDiv.innerHTML = `
        <div style="font-size:18px;font-weight:bold;margin-bottom:10px;">${titleText}</div>
        <div style="font-size:14px;margin-bottom:5px;"><strong>Risk Score:</strong> ${data.score}%</div>
        <div style="font-size:14px;margin-bottom:5px;"><strong>Confidence:</strong> ${data.confidence}</div>
        <div style="font-size:14px;margin-bottom:15px;"><strong>Detected via:</strong> ${sourceText}</div>
        <div style="display:flex;gap:10px;">
            <button id="fjd-details-btn" style="flex:1;padding:8px 12px;background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.4);border-radius:5px;cursor:pointer;font-weight:bold;">More Details</button>
            <button id="fjd-close-btn" style="padding:8px 15px;background:transparent;color:white;border:1px solid rgba(255,255,255,0.4);border-radius:5px;cursor:pointer;font-weight:bold;">✕</button>
        </div>
    `;

    document.body.appendChild(alertDiv);

    document.getElementById("fjd-close-btn").onclick = () => alertDiv.remove();
    document.getElementById("fjd-details-btn").onclick = () => {
        chrome.storage.local.set({ "fakeJobAnalysisDetails": data }, () => {
            chrome.runtime.sendMessage({ action: "open_details_page" });
        });
        alertDiv.remove();
    };

    // Auto-dismiss after 15 seconds
    setTimeout(() => { if (document.body.contains(alertDiv)) alertDiv.remove(); }, 15000);
}

// ── Listen for manual trigger from popup ──
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "extract_job_info") {
        const { jobTitle, companyName, descText } = extractJobData();
        sendResponse({
            title: jobTitle || document.title,
            company: companyName || "Unknown Company",
            description: descText || document.body.innerText.substring(0, 5000)
        });
    }
    return true;
});

// ── Auto-trigger on page load ──
// Small delay so dynamic content (React/JS-rendered pages) has time to mount
setTimeout(extractAndAnalyze, 1500);
