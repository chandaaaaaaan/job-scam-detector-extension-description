"""
company_research.py  (v4 — No API Keys Required)
Scrapes real public reviews from:
  1. Trustpilot    — star rating + real review texts (direct scrape)
  2. AmbitionBox   — Indian company reviews (direct scrape)
  3. Glassdoor     — via DuckDuckGo snippet extraction
  4. Wikipedia     — company background / description
  5. DuckDuckGo    — fallback description

All review sources run in parallel via threading for speed.
"""

import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
TIMEOUT = 7


# ─────────────────────────────────────────────
# 1. TRUSTPILOT  (direct scrape)
# ─────────────────────────────────────────────

def _trustpilot_reviews(company_name: str) -> list:
    """
    Search Trustpilot for the company, then scrape real reviews.
    No API key needed — uses their public search + profile pages.
    """
    results = []
    try:
        # Step 1: Search Trustpilot for the company
        search_url = "https://www.trustpilot.com/search"
        resp = requests.get(
            search_url,
            params={"query": company_name},
            headers=HEADERS,
            timeout=TIMEOUT
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find first result link
        first_link = soup.select_one("a[href*='/review/']")
        if not first_link:
            return []

        profile_path = first_link.get("href", "")
        profile_url = f"https://www.trustpilot.com{profile_path}" if profile_path.startswith("/") else profile_path

        # Step 2: Fetch the profile page
        profile_resp = requests.get(profile_url, headers=HEADERS, timeout=TIMEOUT)
        profile_soup = BeautifulSoup(profile_resp.text, "html.parser")

        # Extract overall rating
        rating_el = (
            profile_soup.select_one("[data-rating-typography]") or
            profile_soup.select_one(".typography_heading-m__T_L_X") or
            profile_soup.find("p", string=re.compile(r"^\d\.\d$"))
        )
        rating_count_el = profile_soup.select_one("[data-reviews-count-typography]")

        if rating_el:
            rating_txt = rating_el.get_text(strip=True)
            count_txt = rating_count_el.get_text(strip=True) if rating_count_el else ""
            suffix = f" ({count_txt} reviews)" if count_txt else ""
            results.append(f"⭐ Trustpilot Rating: {rating_txt}/5{suffix}")

        # Extract review cards
        review_cards = profile_soup.select("article[class*='reviewCard'], section[class*='reviewCard'], div[data-service-review-card-paper]")
        
        # Fallback selectors if above don't match
        if not review_cards:
            review_cards = profile_soup.select(".styles_reviewCardInner__EwDq2, [class*='styles_reviewCard']")

        for card in review_cards[:4]:
            # Try multiple content selectors
            text_el = (
                card.select_one("p[class*='typography_body']") or
                card.select_one("p[data-service-review-text-typography='true']") or
                card.select_one("p")
            )
            if text_el:
                text = text_el.get_text(" ", strip=True)
                if len(text) > 25:
                    short = text[:220] + ("..." if len(text) > 220 else "")
                    results.append(f"[Trustpilot] {short}")

    except Exception:
        pass
    return results


# ─────────────────────────────────────────────
# 2. AMBITIONBOX  (direct scrape — best for Indian companies)
# ─────────────────────────────────────────────

def _ambitionbox_reviews(company_name: str) -> list:
    """Scrape AmbitionBox for employee reviews and ratings."""
    results = []
    try:
        # Build slug from company name
        slug = re.sub(r'[^a-z0-9]+', '-', company_name.lower()).strip('-')

        # Try direct company URL formats
        urls_to_try = [
            f"https://www.ambitionbox.com/reviews/{slug}-reviews",
            f"https://www.ambitionbox.com/reviews/{slug}-company-reviews",
        ]

        profile_soup = None
        for url in urls_to_try:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                if resp.status_code == 200 and "reviews" in resp.text.lower():
                    profile_soup = BeautifulSoup(resp.text, "html.parser")
                    break
            except Exception:
                continue

        if not profile_soup:
            # Fallback: search AmbitionBox
            search_resp = requests.get(
                "https://www.ambitionbox.com/api/v2/search",
                params={"query": company_name, "type": "company"},
                headers={**HEADERS, "Accept": "application/json"},
                timeout=TIMEOUT
            )
            if search_resp.status_code == 200:
                data = search_resp.json()
                companies = data.get("data", {}).get("companies", [])
                if companies:
                    company_slug = companies[0].get("slug", slug)
                    url = f"https://www.ambitionbox.com/reviews/{company_slug}-reviews"
                    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                    if resp.status_code == 200:
                        profile_soup = BeautifulSoup(resp.text, "html.parser")

        if not profile_soup:
            return []

        # Extract overall rating
        rating_el = profile_soup.select_one(".rating-heading, .companyAvgRating, [class*='rating__heading']")
        if rating_el:
            results.append(f"⭐ AmbitionBox Rating: {rating_el.get_text(strip=True)}/5")

        # Extract review snippets
        for card in profile_soup.select(".review-single, .review-tiles__item, [class*='review']")[:4]:
            pros = card.select_one("[class*='pros'], .pros")
            cons = card.select_one("[class*='cons'], .cons")
            text_el = card.select_one("p, .review-description")

            if pros or cons:
                text = ""
                if pros:
                    text += f"Pros: {pros.get_text(' ', strip=True)[:100]}. "
                if cons:
                    text += f"Cons: {cons.get_text(' ', strip=True)[:100]}"
                if len(text.strip()) > 20:
                    results.append(f"[AmbitionBox] {text.strip()}")
            elif text_el:
                text = text_el.get_text(" ", strip=True)
                if len(text) > 25:
                    results.append(f"[AmbitionBox] {text[:220]}")

    except Exception:
        pass
    return results


# ─────────────────────────────────────────────
# 3. GLASSDOOR VIA DDG  (fast snippet extraction)
# ─────────────────────────────────────────────

def _glassdoor_snippets(company_name: str) -> list:
    """
    Uses DuckDuckGo HTML to extract Glassdoor, Indeed, G2 snippets.
    Fast and reliable — no JS required.
    """
    snippets = []
    try:
        query = f'"{company_name}" reviews employees site:glassdoor.com OR site:indeed.com OR site:g2.com OR site:comparably.com'
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        review_sites = ["glassdoor", "indeed", "g2.com", "comparably", "ambitionbox"]

        for result in soup.select(".result"):
            url_tag = result.select_one(".result__url")
            snippet_tag = result.select_one(".result__snippet")
            if not url_tag or not snippet_tag:
                continue
            url_text = url_tag.get_text(strip=True).lower()
            matched_site = next((s for s in review_sites if s in url_text), None)
            if matched_site:
                snippet = snippet_tag.get_text(" ", strip=True)
                if len(snippet) > 40:
                    label = matched_site.title().replace(".Com", "").replace("G2", "G2")
                    snippets.append(f"[{label}] {snippet[:230]}")
            if len(snippets) >= 4:
                break
    except Exception:
        pass
    return snippets


# ─────────────────────────────────────────────
# 4. WIKIPEDIA  (company description)
# ─────────────────────────────────────────────

def _wikipedia_company_data(company_name: str) -> dict:
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        search_resp = requests.get(search_url, params={
            "action": "query",
            "list": "search",
            "srsearch": f"{company_name} company",
            "format": "json",
            "srlimit": 3,
        }, headers=HEADERS, timeout=TIMEOUT)
        hits = search_resp.json().get("query", {}).get("search", [])
        if not hits:
            return {}

        page_title = hits[0]["title"]
        safe_title = page_title.replace(" ", "_")

        summary_resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}",
            headers=HEADERS, timeout=TIMEOUT
        )
        meta = summary_resp.json() if summary_resp.status_code == 200 else {}

        content_resp = requests.get(search_url, params={
            "action": "query",
            "titles": page_title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
        }, headers=HEADERS, timeout=TIMEOUT)
        pages = content_resp.json().get("query", {}).get("pages", {})
        raw = next(iter(pages.values())).get("extract", "")

        return {
            "summary": meta.get("extract", "") or raw[:600],
            "raw_extract": raw,
        }
    except Exception:
        return {}


def _extract_infobox_facts(raw_text: str) -> dict:
    facts = {}
    m = re.search(r'founded\s+(?:in\s+)?(\d{4})', raw_text, re.IGNORECASE)
    if m:
        facts["founded"] = m.group(1)
    m = re.search(r'headquartered?\s+(?:in\s+)?([\w\s,]+?)(?:\.|,\s*\w+\s+(?:is|was|has))', raw_text, re.IGNORECASE)
    if m:
        facts["headquarters"] = m.group(1).strip()
    m = re.search(r'(?:CEO|chief executive|president)\s+(?:is\s+)?([A-Z][a-z]+ [A-Z][a-z]+)', raw_text, re.IGNORECASE)
    if m:
        facts["ceo"] = m.group(1).strip()
    m = re.search(r'([\d,]+(?:\+|\s*thousand|\s*million)?)\s+employees', raw_text, re.IGNORECASE)
    if m:
        facts["employees"] = m.group(1).strip()
    return facts


def _ddg_instant(company_name: str) -> str:
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": company_name, "format": "json", "no_html": 1, "skip_disambig": 1},
            headers=HEADERS, timeout=TIMEOUT
        )
        data = resp.json()
        return data.get("AbstractText", "") or data.get("Answer", "")
    except Exception:
        return ""


# ─────────────────────────────────────────────
# 5. PUBLIC API — MAIN ENTRY POINTS
# ─────────────────────────────────────────────

def get_company_description(company_name: str) -> str:
    """Returns rich structured company overview string."""
    if not company_name or company_name.lower() in ("unknown company", "unknown", ""):
        return ""
    try:
        wiki = _wikipedia_company_data(company_name)
        if wiki:
            raw = wiki.get("raw_extract", "")
            facts = _extract_infobox_facts(raw)
            summary = wiki.get("summary", "")

            lines = []
            if facts.get("founded"):
                lines.append(f"📅 Founded: {facts['founded']}")
            if facts.get("headquarters"):
                lines.append(f"🏢 HQ: {facts['headquarters']}")
            if facts.get("ceo"):
                lines.append(f"👤 CEO: {facts['ceo']}")
            if facts.get("employees"):
                lines.append(f"👥 Employees: {facts['employees']}")

            header = "  |  ".join(lines) if lines else ""
            body = summary[:800] if summary else ""

            if header and body:
                return f"{header}\\n\\n{body}"
            elif body:
                return body
            elif header:
                return header

        abstract = _ddg_instant(company_name)
        if abstract:
            return abstract
    except Exception:
        pass
    return ""


def get_company_reviews(company_name: str) -> list:
    """
    Fetch real reviews from Trustpilot, AmbitionBox, and Glassdoor/Indeed
    all running in parallel via threading. No API keys required.
    Returns up to 7 review strings.
    """
    if not company_name or company_name.lower() in ("unknown company", "unknown", ""):
        return []

    all_reviews = []

    # Run all 3 scrapers in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_trustpilot_reviews, company_name): "trustpilot",
            executor.submit(_ambitionbox_reviews, company_name): "ambitionbox",
            executor.submit(_glassdoor_snippets, company_name): "glassdoor",
        }
        for future in as_completed(futures, timeout=9):
            try:
                result = future.result()
                all_reviews.extend(result)
            except Exception:
                pass

    # Deduplicate, prioritize rating lines first
    seen = set()
    ratings = []
    reviews = []
    for r in all_reviews:
        key = r[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        if re.search(r'rating|\/5', r, re.IGNORECASE) and len(r) < 80:
            ratings.append(r)
        else:
            reviews.append(r)

    combined = ratings + reviews
    return combined[:7]
