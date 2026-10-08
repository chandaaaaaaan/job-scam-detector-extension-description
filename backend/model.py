import re
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

SUSPICIOUS_KEYWORDS = [
    "pay fee", "registration fee", "urgent hiring", 
    "work from home no experience", "earn money fast", "whatsapp only", 
    "no interview", "security deposit", "investment required",
    "payment before joining", "bank account details", "quick money"
]

def analyze_job(description):
    """
    Analyzes the job description for suspicious keywords.
    Returns a dictionary with label, score, confidence, reasons, and highlighted words.
    """
    if not description:
         return {
            "label": "Real",
            "score": 0,
            "confidence": "High",
            "reasons": [],
            "source": "model",
            "highlight_words": []
        }

    description_lower = description.lower()
    found_keywords = []
    
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in description_lower:
            found_keywords.append(keyword)
            
    # Calculate Risk Score (0 - 100)
    # Let's say each keyword adds 25 to the score, max 100
    risk_score = min(len(found_keywords) * 25, 100)
    
    if risk_score >= 75:
        label = "Fake"
        confidence = "High"
    elif risk_score >= 50:
        label = "Fake"
        confidence = "Medium"
    elif risk_score > 0:
        label = "Real"
        confidence = "Medium"
    else:
        label = "Real"
        confidence = "High"
        
    return {
        "label": label,
        "score": risk_score,
        "confidence": confidence,
        "job_issues": [f"Suspicious phrase found: '{kw}'" for kw in found_keywords],
        "company_issues": ["Fallback keyword system does not analyze company context deeply."],
        "reasons": [f"Suspicious phrase found: '{kw}'" for kw in found_keywords],
        "source": "model",
        "highlight_words": found_keywords
    }

def analyze_with_llm(job_description, company_name, reports_count, job_spam_count=0, nlp_data=None):
    if not API_KEY or API_KEY == "your_api_key_here":
        print("API Key not found or default, falling back to keyword model.")
        return analyze_job(job_description)

    if nlp_data is None: nlp_data = {}
    free_emails = nlp_data.get("free_emails", [])
    urls = nlp_data.get("urls", [])
    
    free_email_warning = f"WARNING: Free email addresses detected ({', '.join(free_emails)}). Corporate jobs rarely use free emails!" if free_emails else "No free emails detected in description."
    url_context = f"Found URLs: {', '.join(urls)}." if urls else "No URLs found in description."

    prompt = f"""Analyze this text and determine if it is a FAKE or REAL job posting.
IMPORTANT INSTRUCTION: If the text provided is clearly NOT a job description (e.g., standard generic website text, news, blogs, UI elements), YOU MUST assume it is non-malicious and return "label": "Real" and "score": 0.

Evaluate these ADVANCED HEURISTIC FACTORS intricately:
1. Corporate Reconnaissance (WHOIS/LinkedIn/MCA21 Proxy): Based on your internal knowledge base, does '{company_name}' have a legitimate global footprint, a verifiable domain presence, and a sizable LinkedIn employee base? If it's totally unknown or lacks a corporate footprint, treat it as highly suspicious (Missing Verification).
2. Email & Domain Check: {free_email_warning} {url_context} If a free email (gmail, yahoo) is used for a corporate job, penalize strictly!
3. Cross Verification Tracking: This company has posted {job_spam_count} entirely different jobs recently. If this number is high (>3) for an unknown company, heavily weigh this as a mass-spam duplicate operation!
4. Hidden Red Flags: Look strictly for slight urgency tones ("act fast", "hiring immediately"), overpromising un-realistic salaries, missing technical steps, or painfully generic descriptions.
5. Behavioral Signals (High Risk): Penalize heavily if they mention contacting them on "WhatsApp" or "Telegram", asking for an initial payment/fee, or asking for sensitive bank details!
6. Crowd Intelligence: This company has been flagged {reports_count} times by users.

CRITICAL SAFEGUARD: If the company is highly reputable or globally recognized (e.g., Accenture, Google) and the ONLY anomalies are minor job description typos (like strange education requirements or conflicting years of experience), DO NOT flag it as a scam. Keep the score low. Only assign high scores for genuine malicious traits (asking for money, fake domains, sketchy contact info).

Company: {company_name}
Description: {job_description}

Return ONLY valid JSON with this exact structure:
{{
  "label": "Fake" or "Real",
  "score": 0 to 100,
  "confidence": "Low", "Medium", or "High",
  "job_issues": ["specific issue regarding the job description 1", "issue 2"],
  "company_issues": ["specific suspicious detail about the company 1", "issue 2"],
  "company_background": "A brief 2-sentence description of the company, its history, how long it has been operating, and whether it appears universally recognized/legitimate.",
  "reasons": ["general reason 1 (if Fake, why it's a scam. If Real, provide POSITIVE FEEDBACK about why it looks safe and credible)"],
  "highlight_words": ["word1", "word2"]
}}"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert in detecting job scams. Output valid JSON only. Consider description, company, and reports carefully."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=12)
        response.raise_for_status()
        data = response.json()
        
        content = data['choices'][0]['message']['content']
        # Extract JSON if markdown wrapped
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        result = json.loads(content.strip())
        
        return {
            "label": result.get("label", "Real"),
            "score": result.get("score", 0),
            "confidence": result.get("confidence", "Medium"),
            "job_issues": result.get("job_issues", []),
            "company_issues": result.get("company_issues", []),
            "company_background": result.get("company_background", "Company information unverified."),
            "reasons": result.get("reasons", []),
            "source": "llm",
            "highlight_words": result.get("highlight_words", result.get("suspicious_words", []))
        }
    except Exception as e:
        print(f"LLM API Failed: {e}, falling back to keyword model.")
        return analyze_job(job_description)
