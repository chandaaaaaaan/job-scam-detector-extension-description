document.addEventListener("DOMContentLoaded", () => {
    chrome.storage.local.get("fakeJobAnalysisDetails", (result) => {
        const data = result.fakeJobAnalysisDetails;
        const appRoot = document.getElementById("app-root");
        
        if (!data) {
            appRoot.innerHTML = `<h2 class="text-center text-ignition-theme font-headline text-2xl mt-20">NO_DATA_STREAM_FOUND</h2>`;
            return;
        }

        const isFake = data.label === "Fake";
        if (!isFake) {
            document.body.classList.add("theme-safe");
        }

        const statusTitle = isFake ? "Might be Scam" : "Looks Good";
        const statusSub = isFake 
            ? "Our analysis identified issues with this job posting. We suggest high caution before applying or providing personal details."
            : "No abnormal patterns or common scam traits were found within this posting.";
        
        const bannerLabel = isFake ? "Threat Detected" : "Clearance Granted";
        
        // Calculate the circular meter offset based on Score
        // Circumference of r=48% in a 100x100 box is approx 301. Score is backward offset from 301.
        // Formula: 301 - (301 * score / 100)
        let strokeDashoffset = Math.max(0, 301 - (301 * (data.score / 100)));

        // --- AREA 1: JOB DESCRIPTION MODULES ---
        let jobModulesHtml = "";
        let jIssues = data.job_issues && data.job_issues.length > 0 ? data.job_issues : data.reasons;
        
        if (jIssues && jIssues.length > 0 && isFake) {
            jIssues.forEach((issue, idx) => {
                jobModulesHtml += `
                    <div class="bg-surface-container-low p-6 border-l-2 border-ignition-theme relative group transition-all hover:bg-surface-container-highest">
                        <div class="flex items-center gap-2 mb-4">
                            <span class="material-symbols-outlined text-ignition-theme text-lg">warning</span>
                            <span class="font-headline text-xs font-bold tracking-widest text-on-surface uppercase text-ignition-theme">Anomaly_${idx+1}</span>
                        </div>
                        <p class="text-sm text-on-surface-variant mb-6 font-body">${issue}</p>
                        <div class="flex justify-between items-end border-t border-outline-variant/10 pt-4">
                            <div>
                                <span class="text-[10px] text-outline block uppercase font-bold">Confidence Engine</span>
                                <span class="text-sm font-headline font-bold text-ignition-theme">AI_MATCH: HIGH</span>
                            </div>
                        </div>
                    </div>`;
            });
        } else if (!isFake && data.positive_reports && data.positive_reports.length > 0) {
            data.positive_reports.forEach((issue, idx) => {
                jobModulesHtml += `
                    <div class="bg-surface-container-low p-6 border-l-2 border-ignition-theme relative group transition-all hover:bg-surface-container-highest">
                        <div class="flex items-center gap-2 mb-4">
                            <span class="material-symbols-outlined text-ignition-theme text-lg">verified_user</span>
                            <span class="font-headline text-xs font-bold tracking-widest text-on-surface uppercase text-ignition-theme">Safe_Anchor_${idx+1}</span>
                        </div>
                        <p class="text-sm text-on-surface-variant mb-6 font-body">${issue}</p>
                    </div>`;
            });
        } else {
             jobModulesHtml += `
             <div class="bg-surface-container-low p-6 border-l-2 border-ignition-theme">
                 <p class="text-sm text-on-surface-variant font-body">No critical anomalies isolated across textual vectors.</p>
             </div>`;
        }

        // --- AREA 2: COMPANY INTEL ---
        let companyModulesHtml = "";
        if (data.company_issues && data.company_issues.length > 0 && isFake) {
            data.company_issues.forEach(issue => {
                companyModulesHtml += `<div class="bg-surface-container-low p-4"><span class="text-[10px] text-outline uppercase font-bold block mb-1">Flag</span><span class="font-headline text-xs text-ignition-theme font-bold uppercase">${issue}</span></div>`;
            });
        } else {
            companyModulesHtml += `<div class="bg-surface-container-low p-4"><span class="text-[10px] text-outline uppercase font-bold block mb-1">Status</span><span class="font-headline text-xs text-ignition-theme font-bold uppercase">VERIFIED_TRACE</span></div>`;
        }

        // --- AREA 3: COMPANY BACKGROUND ---
        let flagCount = isFake ? data.report_count : 0;
        let reportText = isFake ? `Flagged ${flagCount} Times` : "Zero Threat Reports";
        
        let companyBackgroundText = data.company_background || "Background intelligence gathering failed or was incomplete. No additional corporate history found.";

        // Community Feedback (from DB or user reports)
        let allFeedbacks = [];
        if (data.company_reports && data.company_reports.length > 0) {
            data.company_reports.slice(0, 3).forEach(r => allFeedbacks.push({text: r, type: 'bad'}));
        }
        if (data.positive_reports && data.positive_reports.length > 0) {
            data.positive_reports.slice(0, 3).forEach(r => allFeedbacks.push({text: r, type: 'good'}));
        }

        // Build feedback cards (always render — show empty state if none)
        let feedbackCardsHtml = "";
        if (allFeedbacks.length > 0) {
            allFeedbacks.forEach(feedback => {
                let fullReport = feedback.text;
                let iconName = feedback.type === 'bad' ? "memory" : "verified";
                let iconColor = feedback.type === 'bad' ? "text-ignition-theme" : "text-emerald-400";
                let iconBg   = feedback.type === 'bad' ? "bg-ignition-theme/10" : "bg-emerald-400/10";
                feedbackCardsHtml += `
                <div class="bg-surface-container-lowest p-4 border border-outline-variant/10 flex items-start gap-4 group hover:bg-surface-container-low transition-all">
                    <div class="w-8 h-8 flex items-center justify-center shrink-0 ${iconBg}">
                        <span class="material-symbols-outlined text-sm ${iconColor}">${iconName}</span>
                    </div>
                    <div class="flex-1">
                        <div class="text-[10px] font-bold font-headline ${feedback.type === 'bad' ? 'text-ignition-theme' : 'text-emerald-400'} uppercase mb-1">${feedback.type === 'bad' ? 'SCAM_REPORT' : 'POSITIVE_REPORT'}</div>
                        <div class="text-xs font-body text-on-surface-variant italic leading-relaxed">"${fullReport}"</div>
                    </div>
                </div>`;
            });
        } else {
            feedbackCardsHtml = `
            <div class="col-span-full flex flex-col items-center justify-center py-10 gap-4">
                <div class="w-14 h-14 rounded-full bg-slate-500/10 border border-slate-500/20 flex items-center justify-center">
                    <span class="material-symbols-outlined text-2xl text-slate-400">balance</span>
                </div>
                <div class="text-center">
                    <p class="text-sm font-headline font-bold text-slate-400 uppercase tracking-[0.2em] mb-1">Neutral Feedback</p>
                    <p class="text-xs font-body text-on-surface-variant opacity-60">No scam reports or community reviews found for this company.</p>
                </div>
                <div class="flex items-center gap-2 px-4 py-1.5 border border-slate-500/20 bg-slate-500/5">
                    <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                    <span class="text-[10px] font-headline text-slate-400 uppercase tracking-widest">Insufficient Data — Proceed With Caution</span>
                </div>
            </div>`;
        }

        // Live Reviews — smart render: detect rating lines vs review quotes
        let liveReviewsHtml = "";
        let ratingBadgesHtml = "";
        if (data.live_reviews && data.live_reviews.length > 0) {
            data.live_reviews.forEach(review => {
                // Detect rating summary lines (e.g. "⭐ Google Rating: 4.2/5 (1,200 reviews)")
                const isRatingLine = /rating|\/5/i.test(review) && review.length < 80;
                if (isRatingLine) {
                    const isGoogle = /google/i.test(review);
                    const isTrustpilot = /trustpilot/i.test(review);
                    const badgeColor = isGoogle ? "text-yellow-400 border-yellow-400/30 bg-yellow-400/5"
                                     : isTrustpilot ? "text-green-400 border-green-400/30 bg-green-400/5"
                                     : "text-cyan-400 border-cyan-400/30 bg-cyan-400/5";
                    const icon = isGoogle ? "map" : isTrustpilot ? "verified" : "star_rate";
                    ratingBadgesHtml += `
                    <div class="flex items-center gap-2 px-4 py-2 border ${badgeColor} rounded-none">
                        <span class="material-symbols-outlined text-sm">${icon}</span>
                        <span class="font-headline text-xs font-bold uppercase tracking-wider">${review}</span>
                    </div>`;
                } else {
                    // Extract source label from [Glassdoor] prefix if present
                    const srcMatch = review.match(/^\[([^\]]+)\]\s*/);
                    const srcLabel = srcMatch ? srcMatch[1] : "Live Review";
                    const cleanReview = srcMatch ? review.slice(srcMatch[0].length) : review;
                    const srcColor = /glassdoor/i.test(srcLabel) ? "text-emerald-400"
                                   : /indeed/i.test(srcLabel) ? "text-blue-400"
                                   : /trustpilot/i.test(srcLabel) ? "text-green-400"
                                   : /ambitionbox/i.test(srcLabel) ? "text-orange-400"
                                   : "text-cyan-400";
                    liveReviewsHtml += `
                    <div class="bg-surface-container-lowest p-4 border border-outline-variant/10 flex items-start gap-4 group hover:bg-surface-container-low transition-all">
                        <div class="w-8 h-8 flex items-center justify-center shrink-0 bg-cyan-400/10">
                            <span class="material-symbols-outlined text-sm text-cyan-400">rate_review</span>
                        </div>
                        <div class="flex-1">
                            <div class="text-[10px] font-bold font-headline ${srcColor} uppercase mb-1">${srcLabel.toUpperCase()}</div>
                            <div class="text-xs font-body text-on-surface-variant leading-relaxed italic">${cleanReview}</div>
                        </div>
                    </div>`;
                }
            });
        }


        let html = `
            <!-- Background Decorative Element -->
            <div class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-ignition-theme/10 rounded-full blur-[120px] pointer-events-none -z-10"></div>

            <!-- Header: Risk Score Widget -->
            <section class="flex flex-col md:flex-row items-center gap-12 mb-16">
                <div class="relative group cursor-crosshair">
                    <div class="w-64 h-64 rounded-full glass-orb border border-ignition-theme/20 flex flex-col items-center justify-center relative overflow-hidden backdrop-blur-2xl">
                        <!-- Radial Gauge Simulation -->
                        <svg class="absolute inset-0 w-full h-full -rotate-90">
                            <circle cx="50%" cy="50%" fill="none" r="48%" stroke="rgba(var(--theme-color-rgb), 0.1)" stroke-width="2"></circle>
                            <circle class="threat-glow" cx="50%" cy="50%" fill="none" r="48%" stroke="var(--theme-color-hex)" stroke-dasharray="301" stroke-dashoffset="301" stroke-width="4" id="circle-meter"></circle>
                        </svg>
                        
                        <div class="text-ignition-theme font-headline font-bold text-5xl tracking-tighter mb-1">${data.score}%</div>
                        <div class="text-ignition-theme/60 font-headline text-[10px] tracking-[0.3em] font-bold">RISK_SCORE</div>
                        
                        <!-- Micro-telemetry -->
                        <div class="absolute bottom-10 flex gap-1">
                            <div class="w-1 h-1 bg-ignition-theme"></div>
                            <div class="w-1 h-1 bg-ignition-theme"></div>
                            <div class="w-1 h-1 bg-ignition-theme/30"></div>
                        </div>
                    </div>
                    <!-- Floating labels around orb -->
                    <div class="absolute -top-4 -right-8 bg-surface-container-highest px-3 py-1 border-l-2 border-ignition-theme">
                        <span class="text-[10px] font-headline text-ignition-theme font-bold">${data.confidence.replace(/ /g, "_").toUpperCase()}</span>
                    </div>
                </div>

                <div class="flex-1 space-y-4 text-center md:text-left">
                    <div class="inline-flex items-center gap-2 px-3 py-1 bg-ignition-theme/10 text-ignition-theme border border-ignition-theme/20 mb-2">
                        <span class="w-2 h-2 bg-ignition-theme animate-pulse"></span>
                        <span class="font-headline text-xs font-bold tracking-widest uppercase">${bannerLabel}</span>
                    </div>
                    <h2 class="font-headline text-4xl md:text-6xl font-bold uppercase tracking-tight leading-none text-on-surface mb-2">
                        <span class="text-ignition-theme">${statusTitle}</span>
                    </h2>
                    <p class="text-on-surface-variant max-w-xl font-body text-sm leading-relaxed">${statusSub}</p>
                    <div class="flex flex-wrap gap-4 pt-4 justify-center md:justify-start">
                        <div class="bg-surface-container-low px-4 py-2 border-l border-outline-variant">
                            <div class="text-[10px] text-outline uppercase font-bold tracking-tighter">ALGORITHM</div>
                            <div class="font-headline text-sm font-bold text-on-surface uppercase">${data.source.replace("_", " ")}</div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Bento Grid Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <!-- Section 1: Linguistic Anomalies -->
                <div class="lg:col-span-7 space-y-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-3 h-[1px] bg-primary"></div>
                        <h3 class="font-headline text-xs font-bold tracking-[0.2em] text-primary uppercase">JOB_DESCRIPTION_ANALYSIS</h3>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        ${jobModulesHtml}
                    </div>
                </div>

                <!-- Section 2 & 3: Right Column -->
                <div class="lg:col-span-5 space-y-8">
                    
                    <!-- Tactical Grid: Company Intelligence -->
                    <div>
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-3 h-[1px] bg-primary"></div>
                            <h3 class="font-headline text-xs font-bold tracking-[0.2em] text-primary uppercase">COMPANY_INTEL</h3>
                        </div>
                        <div class="bg-surface-container-lowest border border-outline-variant/10 p-1">
                            <div class="grid grid-cols-2 gap-px bg-outline-variant/10">
                                ${companyModulesHtml}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Company Background Info -->
                    <div>
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-3 h-[1px] bg-primary"></div>
                            <h3 class="font-headline text-xs font-bold tracking-[0.2em] text-primary uppercase">COMPANY_OVERVIEW</h3>
                        </div>
                        <div class="space-y-3">
                            <div class="bg-ignition-theme/5 p-4 border-r-2 border-ignition-theme flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <span class="material-symbols-outlined text-ignition-theme">flag</span>
                                    <span class="font-headline text-lg font-bold text-ignition-theme">${reportText}</span>
                                </div>
                                <span class="text-[10px] font-headline text-ignition-theme font-bold">BY_PEER_SYSTEMS</span>
                            </div>
                            
                            <!-- Corporate History -->
                            <!-- Corporate History -->
                            <div class="bg-surface-container-lowest p-4 border border-outline-variant/10">
                                <div class="flex items-center gap-2 mb-3">
                                    <span class="material-symbols-outlined text-xs text-on-surface-variant">info</span>
                                    <div class="text-[10px] font-bold font-headline text-on-surface uppercase block">Corporate History & Legitimacy</div>
                                </div>
                                ${(() => {
                                    const raw = companyBackgroundText;
                                    const parts = raw.split('\\n\\n');
                                    const metaLine = parts.length > 1 ? parts[0] : '';
                                    const bodyText = parts.length > 1 ? parts.slice(1).join(' ') : raw;
                                    let pillsHtml = '';
                                    if (metaLine) {
                                        const pills = metaLine.split('  |  ').map(p => p.trim()).filter(Boolean);
                                        pillsHtml = `<div class="flex flex-wrap gap-2 mb-3">${pills.map(p => `<span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] bg-surface-container-highest border border-outline-variant/20 font-headline text-on-surface">${p}</span>`).join('')}</div>`;
                                    }
                                    return `${pillsHtml}<p class="text-sm font-body text-on-surface-variant leading-relaxed">${bodyText}</p>`;
                                })()}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ===== COMMUNITY FEEDBACK SECTION (always visible) ===== -->
            <div class="mt-10">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-3 h-[1px] bg-primary"></div>
                    <h3 class="font-headline text-xs font-bold tracking-[0.2em] text-primary uppercase">COMMUNITY_FEEDBACK</h3>
                    <div class="ml-auto flex items-center gap-2 px-3 py-1 bg-surface-container-low border border-outline-variant/20">
                        <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                        <span class="text-[10px] font-headline text-cyan-400 uppercase tracking-widest">LIVE_FEED</span>
                    </div>
                </div>

                <!-- Rating Badges (Google/Trustpilot rating summary) -->
                ${ratingBadgesHtml ? `
                <div class="flex flex-wrap gap-3 mb-5">
                    ${ratingBadgesHtml}
                </div>` : ''}

                <!-- Community Feedback Cards Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                    ${feedbackCardsHtml}
                </div>

                ${liveReviewsHtml ? `
                <div class="mb-6">
                    <div class="text-[10px] font-bold font-headline text-cyan-400 uppercase mb-3 opacity-70 tracking-widest">Live Reviews — Google · Trustpilot · Glassdoor · Indeed</div>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        ${liveReviewsHtml}
                    </div>
                </div>` : ''}
            </div>
        `;

        appRoot.innerHTML = html;
        
        // Let CSS Render, then trigger circular meter animation
        setTimeout(() => {
             const circleMeter = document.getElementById("circle-meter");
             if (circleMeter) {
                 circleMeter.style.strokeDashoffset = strokeDashoffset;
             }
        }, 100);
    });
});
