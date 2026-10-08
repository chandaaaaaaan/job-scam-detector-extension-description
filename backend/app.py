from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import database
import model
import nlp_ml
import company_research

app = Flask(__name__)
# Enable CORS for all routes (important for Chrome Extension)
CORS(app)

# Initialize database on startup
database.init_db()

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    company_name = data.get('company_name', '').strip()
    job_title = data.get('job_title', '').strip()
    description = data.get('description', '').strip()

    # Step 1: Check Database first (Memory-Based)
    memory_result = database.check_memory(company_name, job_title)
    report_count = database.get_report_count(company_name)

    if memory_result:
        memory_result["report_count"] = report_count
        memory_result["company_reports"] = database.get_company_reports(company_name)
        memory_result["positive_reports"] = database.get_company_positive_feedback(company_name)
        if "confidence" not in memory_result:
            score = memory_result.get("score", 0)
            memory_result["confidence"] = "High" if score >= 60 else ("Medium" if score >= 40 else "Low")
        return jsonify(memory_result)

    # Step 2: Not found in memory, run the ML and NLP layers
    nlp_data = nlp_ml.extract_nlp_features(description)
    ml_score = nlp_ml.analyze_with_ml(description)
    job_spam_count = database.get_company_job_count(company_name)
    
    # Run the LLM Model layer with advanced intelligence
    llm_result = model.analyze_with_llm(description, company_name, report_count, job_spam_count, nlp_data)
    
    # Combine ALL into Hybrid final score
    analysis_result = nlp_ml.combine_results(llm_result, ml_score, nlp_data)
    analysis_result["report_count"] = report_count
    
    # Attach actual negative feedback from database
    analysis_result["company_reports"] = database.get_company_reports(company_name)
    analysis_result["positive_reports"] = database.get_company_positive_feedback(company_name)
    
    # Step 3: Live Company Research (Website Scraping + Review Snippets)
    # Run in background so we don't block — fetch concurrently via threading
    company_desc_live = company_research.get_company_description(company_name)
    company_reviews = company_research.get_company_reviews(company_name)
    
    # Layer in live data — override LLM hallucination
    if company_desc_live:
        analysis_result["company_background"] = company_desc_live
    if company_reviews:
        if analysis_result.get("label") == "Fake":
            analysis_result["company_reports"] = company_reviews + analysis_result.get("company_reports", [])
        else:
            analysis_result["positive_reports"] = company_reviews + analysis_result.get("positive_reports", [])
    analysis_result["live_reviews"] = company_reviews

    # Step 4: Save scan to memory universally to build historical safe feedback loops natively
    database.save_to_memory(
        company_name, 
        job_title, 
        description, 
        analysis_result['label'], 
        analysis_result['score'], 
        analysis_result['reasons'],
        analysis_result
    )

    # Return Result
    return jsonify(analysis_result)


@app.route('/report', methods=['POST'])
def report_scam():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    company_name = data.get('company_name', '').strip()
    job_title = data.get('job_title', '').strip()
    description = data.get('description', '').strip()

    # User reported as scam
    success = database.save_to_memory(
        company_name,
        job_title,
        description,
        "Fake",
        100,
        ["User reported as scam"],
        {"confidence": "High", "job_issues": [], "company_issues": [], "company_background": "User manual report.", "highlight_words": []}
    )
    
    if success:
        return jsonify({"message": "Successfully reported and saved to memory."}), 200
    else:
        return jsonify({"message": "Already reported."}), 200

@app.route('/dashboard')
def dashboard():
    scams = database.get_all_scams()
    
    # Process and aggregate data for the UI
    companies = {}
    for s in scams:
        comp = s['company_name']
        if comp not in companies:
            companies[comp] = {"reports": 0, "jobs": [], "avg_score": 0, "reasons": set(), "label": s['label']}
        
        companies[comp]["reports"] += 1
        if s['job_title'] not in companies[comp]["jobs"]:
            companies[comp]["jobs"].append(s['job_title'])
        companies[comp]["avg_score"] += s['risk_score']
        for r in s['reasons']: 
             companies[comp]['reasons'].add(r)
            
    for comp in companies:
        companies[comp]["avg_score"] = int(companies[comp]["avg_score"] / companies[comp]["reports"])
        companies[comp]["reasons"] = list(companies[comp]["reasons"])
        
    return render_template('dashboard.html', companies=companies, scams=scams)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
