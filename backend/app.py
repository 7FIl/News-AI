# ==============================================================================
# SECTION 1: IMPORTS
# ==============================================================================
import os
import json
import requests
# MODIFIED: Added send_from_directory
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS 
from dotenv import load_dotenv

# ==============================================================================
# SECTION 2: SETUP AND CONFIGURATION
# ==============================================================================
load_dotenv()
# MODIFIED: Point to the correct static folder (your project's root)
app = Flask(__name__, static_folder='../', static_url_path='/')
CORS(app) 

# --- API Keys & IDs from .env file ---
LUNOS_API_KEY = os.getenv('LUNOS_API_KEY')
UNLI_API_KEY = os.getenv('UNLI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')

# --- Static Config ---
LUNOS_APP_ID = "my-app" 

# --- API Endpoints ---
LUNOS_API_URL = "https://api.lunos.tech/v1/chat/completions"
UNLI_API_URL = "https://api.unli.dev/v1/chat/completions"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# ==============================================================================
# NEW SECTION: ROUTES FOR SERVING FRONTEND FILES
# ==============================================================================

@app.route('/')
def serve_index():
    # Serves the index.html file from the root directory
    return send_from_directory('../', 'index.html')

@app.route('/js/<path:path>')
def serve_js(path):
    # Serves any file from the 'js' directory
    return send_from_directory('../js', path)

@app.route('/css/<path:path>')
def serve_css(path):
    # Serves any file from the 'css' directory
    return send_from_directory('../css', path)


# ==============================================================================
# SECTION 3: HELPER FUNCTIONS (The Three Specialists)
# ==============================================================================

# --- SPECIALIST 1: THE ANALYST (Unli.dev) ---
def extract_claims_with_unli(text_content):
    print("Sending prompt to Unli.dev to extract claims...")
    system_prompt = "You are an expert news analysis assistant. Your sole purpose is to read a news article, extract its key factual claims, and provide a brief summary. Format your entire response as a single, valid JSON object with two keys: 'summary' and 'claims'. Do not add any conversational text."
    user_prompt = f"Please analyze the following news article: {text_content}"
    headers = {'Authorization': f'Bearer {UNLI_API_KEY}', 'Content-Type': 'application/json', 'X-App-ID': LUNOS_APP_ID}
    payload = {'model': 'unli-auto', 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]}
    try:
        response = requests.post(UNLI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_response_data = response.json()
        json_string_content = ai_response_data['choices'][0]['message']['content']
        if json_string_content.strip().startswith("```json"):
            json_string_content = json_string_content.strip()[7:-3]
        parsed_json = json.loads(json_string_content)
        print("Unli.dev analysis successful.")
        return parsed_json
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"ERROR: Failed to process or parse response from Unli.dev. {e}")
        return None

# --- SPECIALIST 2: THE RESEARCHER (Google Search) ---
def google_search_for_claim(claim_text, api_key, search_engine_id):
    print(f"Googling for claim: '{claim_text}'...")
    params = {'key': api_key, 'cx': search_engine_id, 'q': claim_text}
    try:
        response = requests.get(GOOGLE_SEARCH_URL, params=params)
        response.raise_for_status()
        search_results = response.json()
        context = ""
        sources = []
        if 'items' in search_results:
            sources = [item['link'] for item in search_results.get('items', [])[:4]]
            for i, item in enumerate(search_results['items'][:4]):
                context += f"Source [{i+1}]: {item['title']}\nSnippet: {item['snippet']}\nURL: {item['link']}\n\n"
        return context, sources
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Google Search API call failed. {e}")
        return "", []

# --- SPECIALIST 3: THE DETECTIVE (Lunos.ai) ---
def _verify_single_claim_with_lunos(claim_text, search_evidence, search_sources):
    system_prompt = "You are a world-class AI fact-checking detective. Your mission is to determine the validity of a 'Claim' based *solely* on the 'Evidence' provided from recent web search results. Do not use your own internal knowledge. Your response must be a single, valid JSON object with three keys: 'claim', 'verdict', and 'explanation'. The 'explanation' should summarize how the evidence supports your verdict."
    user_prompt = f"Evidence from Google Search:\n---\n{search_evidence}\n---\n\nBased only on the evidence above, please fact-check this claim: \"{claim_text}\""
    headers = {'Authorization': f'Bearer {LUNOS_API_KEY}', 'Content-Type': 'application/json', 'X-App-ID': LUNOS_APP_ID}
    payload = {'model': 'openai/gpt-5', 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]}
    try:
        response = requests.post(LUNOS_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_response_data = response.json()
        json_string_content = ai_response_data['choices'][0]['message']['content']
        if json_string_content.strip().startswith("```json"):
            json_string_content = json_string_content.strip()[7:-3]
        final_json = json.loads(json_string_content)
        final_json['sources'] = search_sources
        return final_json
    except Exception as e:
        print(f"ERROR: Lunos.ai failed to process claim '{claim_text}'. Reason: {e}")
        return {"claim": claim_text, "verdict": "Unverifiable", "explanation": "The fact-checking AI failed to produce a verdict.", "sources": search_sources}

def check_claims_with_lunos(claims_list):
    print(f"Fact-checking {len(claims_list)} claims using Google Search + Lunos.ai...")
    verified_results = []
    for claim in claims_list:
        evidence, sources = google_search_for_claim(claim, GOOGLE_API_KEY, SEARCH_ENGINE_ID)
        if not evidence:
             print(f"No evidence found for claim: '{claim}'. Skipping verification.")
             verified_results.append({"claim": claim, "verdict": "Unverifiable", "explanation": "No relevant search results were found to verify this claim.", "sources": []})
             continue
        result = _verify_single_claim_with_lunos(claim, evidence, sources)
        verified_results.append(result)
    print("Fact-checking loop complete.")
    return {"results": verified_results}

# ==============================================================================
# SECTION 4: THE MAIN API ENDPOINT (The Manager)
# ==============================================================================
@app.route('/check-news', methods=['POST'])
def check_news_endpoint():
    print("\n--- New Request Received at /check-news ---")
    data = request.get_json()
    if not data or 'content' not in data: 
        return jsonify({'error': 'No content provided in the request.'}), 400
    
    news_content = data.get('content')
    analyst_result = extract_claims_with_unli(news_content)
    
    if not analyst_result or 'claims' not in analyst_result:
        return jsonify({'error': 'AI Analyst (Unli.dev) failed to extract claims or returned a malformed response.'}), 500
    
    summary = analyst_result.get('summary', 'No summary available.')
    claims = analyst_result.get('claims', [])
    
    if not claims:
        print("--- Request Complete. No claims found to verify. ---")
        return jsonify({
            'summary': summary,
            'overall_verdict': 'INCONCLUSIVE',
            'counts': {'accurate': 0, 'misleading': 0, 'false': 0, 'unverifiable': 1},
            'details': [{
                'claim': 'No specific claims were identified in the text.',
                'verdict': 'UNVERIFIABLE',
                'explanation': 'The AI analyst could not extract any factual claims to verify from the provided article.',
                'sources': []
            }]
        })

    fact_check_results = check_claims_with_lunos(claims)
    
    details = fact_check_results.get('results', [])
    verdicts = [str(result.get('verdict', 'INCONCLUSIVE')).upper() for result in details]
    total_claims = len(verdicts)
    
    accurate_keywords = ['TRUE', 'ACCURATE']
    misleading_keywords = ['MISLEADING', 'PARTIALLY TRUE']
    false_keywords = ['FALSE', 'INACCURATE']
    
    accurate_count = sum(1 for v in verdicts if any(kw in v for kw in accurate_keywords))
    misleading_count = sum(1 for v in verdicts if any(kw in v for kw in misleading_keywords))
    false_count = sum(1 for v in verdicts if any(kw in v for kw in false_keywords))
    unverifiable_count = total_claims - (accurate_count + misleading_count + false_count)

    overall_verdict = 'INCONCLUSIVE'
    if total_claims > 0:
        if false_count > 0:
            if accurate_count / total_claims >= 0.7:
                overall_verdict = 'MOSTLY ACCURATE'
            elif false_count / total_claims >= 0.7:
                overall_verdict = 'MOSTLY FALSE'
            else:
                overall_verdict = 'MIXED'
        elif misleading_count > 0:
            overall_verdict = 'MISLEADING'
        elif accurate_count == total_claims:
            overall_verdict = 'ACCURATE'
        elif accurate_count > 0:
             overall_verdict = 'ACCURATE'
    
    final_response = {
        'summary': summary, 
        'overall_verdict': overall_verdict, 
        'counts': {
            'accurate': accurate_count,
            'misleading': misleading_count,
            'false': false_count,
            'unverifiable': unverifiable_count
        },
        'details': details
    }
    print("--- Request Complete. Sending final response. ---")
    return jsonify(final_response)

# ==============================================================================
# SECTION 5: RUNNING THE APPLICATION
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
