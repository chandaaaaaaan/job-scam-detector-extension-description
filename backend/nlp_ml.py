import re
import os
import nltk
from nltk import pos_tag, ne_chunk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Ensure NLTK packages are silently loaded or downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('chunkers/maxent_ne_chunker')
    nltk.data.find('corpora/words')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)

# -----------------------------------
# 1. NLP LAYER (Extraction)
# -----------------------------------
def extract_nlp_features(text):
    """
    Extracts keywords, named entities (GPE, ORG, PERSON), emails, and phone numbers.
    """
    results = {
        "entities": [],
        "emails": [],
        "phones": []
    }
    
    if not text:
        return results
        
    # Regex extractions
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    results["emails"] = list(set(emails))
    
    # Free email provider check (Signal: Email Check)
    free_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'mail.com', 'aol.com', 'protonmail.com']
    results["free_emails"] = [e for e in results["emails"] if e.split('@')[-1].lower() in free_providers]
    
    # URL extraction for site footprint proxy
    urls = re.findall(r"https?://[\w\.-]+", text)
    results["urls"] = list(set(urls))
    
    # Simple regex for US/Intl phone numbers
    phones = re.findall(r"\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b", text)
    results["phones"] = list(set(phones))
    
    # NLTK Named Entity Recognition
    try:
        tokens = nltk.word_tokenize(text)
        tags = pos_tag(tokens)
        chunks = ne_chunk(tags)
        
        entities = []
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                entity_name = ' '.join(c[0] for c in chunk)
                entities.append(f"{chunk.label()}: {entity_name}")
                
        results["entities"] = list(set(entities))
    except Exception as e:
        # Fallback if NLTK has issues
        print(f"NLP Entity Extraction warning: {e}")
        
    return results

# -----------------------------------
# 2. ML LAYER (Lightweight Classification)
# -----------------------------------

# We fit a minimal model on some hardcoded examples to act as a "pre-trained" baseline.
_vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
_ml_model = LogisticRegression(random_state=42)

# Training Data
DUMMY_TEXTS = [
    "We are urgently hiring. Please pay the registration fee before no interview.",
    "This is a scam. Whatsapp me for quick money without interview.",
    "Legitimate software engineer role at top tech company. Full benefits, health insurance.",
    "You must pay a security deposit of $100 to bank account details for work from home.",
    "Marketing manager needed. Good salary, standard 9-5 working hours.",
    "Backend Developer requires 5 years Python experience. Remote position, flexible hours. Apply via portal."
]
DUMMY_LABELS = [1, 1, 0, 1, 0, 0] # 1=Fake, 0=Real

_vectorizer.fit(DUMMY_TEXTS)
X_train = _vectorizer.transform(DUMMY_TEXTS)
_ml_model.fit(X_train, DUMMY_LABELS)

def analyze_with_ml(description):
    """
    Takes description text (TF-IDF features) and outputs a probability of scam (0-100 score).
    """
    if not description:
        return 0
        
    # Transform input text
    X_input = _vectorizer.transform([description])
    
    # Predict probability of class 1 (Fake)
    # predict_proba returns [[prob_0, prob_1]]
    prob = _ml_model.predict_proba(X_input)[0][1]
    
    ml_score = int(prob * 100)
    return ml_score

def combine_results(llm_result, ml_score, nlp_data):
    """
    Combine all 3 factors:
    final_score = (LLM_score * 0.6) + (ML_score * 0.4)
    """
    llm_score = llm_result.get("score", 0)
    
    # Weighted calculation
    final_score = int((llm_score * 0.6) + (ml_score * 0.4))
    
    if final_score >= 75:
        label = "Fake"
        confidence = "High Risk (Likely Scam)"
    elif final_score >= 50:
        # User defined: Medium Risk -> Suspicious
        label = "Fake"
        confidence = "Medium Risk (Suspicious)"
    else:
        # User defined: Low Risk -> Likely Real
        label = "Real"
        confidence = "Low Risk (Likely Real)"
        
    combined = {
        "label": label,
        "score": final_score,
        "confidence": confidence,
        "source": "hybrid_ai",
        "job_issues": llm_result.get("job_issues", []),
        "company_issues": llm_result.get("company_issues", []),
        "company_background": llm_result.get("company_background", "Company information unverified."),
        "reasons": llm_result.get("reasons", []),
        "highlight_words": llm_result.get("highlight_words", []),
        
        # Provide granular breakdown back to frontend
        "llm_score": llm_score,
        "ml_score": ml_score,
        "nlp_entities": nlp_data.get("entities", []),
        "nlp_emails": nlp_data.get("emails", []),
        "nlp_phones": nlp_data.get("phones", [])
    }
    
    return combined
