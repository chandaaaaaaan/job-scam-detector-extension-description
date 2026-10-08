import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.1-8b-instant')

prompt = f"""Analyze this text and determine if it is a FAKE or REAL job posting.
IMPORTANT INSTRUCTION: If the text provided is clearly NOT a job description (e.g., standard generic website text, news, blogs, UI elements), YOU MUST assume it is non-malicious and return "label": "Real" and "score": 0.

Evaluate these 5 ADVANCED HEURISTIC FACTORS intricately:
1. Cross Verification Tracking: This company has posted 0 entirely different jobs recently. If this number is high (>3), heavily weigh this as a mass-spam duplicate operation!
2. Hidden Red Flags: Look strictly for slight urgency tones ("act fast", "hiring immediately"), overpromising un-realistic salaries for the role, missing technical steps, or painfully generic descriptions.
3. Behavioral Signals (High Risk): Penalize heavily if they mention contacting them on "WhatsApp" or "Telegram", asking for an initial payment/fee, or asking for sensitive bank/personal details via random unverified emails!
4. Company Details: Name credibility, missing corporate details, weird URLs.
5. Crowd Intelligence: This company has been flagged 0 times by users.

Company: DataTech Solutions
Description: We are seeking a focused professional for a 100% remote data entry role.

Return ONLY valid JSON with this exact structure:
{{
  "label": "Fake" or "Real",
  "score": 0 to 100,
  "confidence": "Low", "Medium", or "High",
  "job_issues": ["specific issue regarding the job description 1", "issue 2"],
  "company_issues": ["specific suspicious detail about the company 1", "issue 2"],
  "reasons": ["general reason 1 (if Fake, why it's a scam. If Real, provide POSITIVE FEEDBACK about why it looks safe and credible)"],
  "highlight_words": ["word1", "word2"]
}}"""

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

payload = {
    "model": LLM_MODEL,
    "messages": [
        {"role": "system", "content": "You are an expert in detecting job scams. Output valid JSON only. Consider description, company, and reports carefully."},
        {"role": "user", "content": prompt}
    ],
    "response_format": {"type": "json_object"}
}

print("Sending request to Groq...", flush=True)
try:
    response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)
    print("Status:", response.status_code, flush=True)
    print("Response JSON:\n", json.dumps(response.json(), indent=2), flush=True)
except Exception as e:
    print("Error:", e, flush=True)
