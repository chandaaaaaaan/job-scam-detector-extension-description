import requests
import json

url = "http://127.0.0.1:5000/analyze"
payload = {
    "company_name": "DataTech Solutions",
    "job_title": "Remote Data Entry Analyst",
    "description": "We are seeking a focused professional for a 100% remote data entry role. The responsibilities include standard spreadsheet management and typing. Salary is extremely generous at $50/hour with unlimited paid time off. Because we are hiring immediately to fill the quota, please reach out directly to our hiring manager on Telegram at @DataTechHR to complete the brief on-boarding module. Act fast as spots are limited."
}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:\n" + json.dumps(response.json(), indent=2))
except Exception as e:
    print(e)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error:", e)
