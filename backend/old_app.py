import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LUNOS_API_KEY = os.getenv('LUNOS_API_KEY')
UNLI_API_KEY = os.getenv('UNLI_API_KEY')
LUNOS_APP_ID = "my-app"

LUNOS_API_URL = "https://api.lunos.tech/v1/chat/completions"
UNLI_API_URL = "https://api.unli.dev/v1/chat/completions" # Updated URL

def extract_claims_with_lunos(text_content):
    # This function remains the same as our last version
    print("Sending prompt to Lunos.tech /chat/completions endpoint...")
    system_prompt = "You are an expert news analysis assistant. Your sole purpose is to read a news article provided by the user, extract its key factual claims, and provide a brief summary. You must format your entire response as a single, valid JSON object containing two keys: 'summary' and 'claims'. Do not add any conversational text or explanations outside of the JSON object."
    user_prompt = f"Please analyze the following news article: {text_content}"
    headers = {'Authorization': f'Bearer {LUNOS_API_KEY}', 'Content-Type': 'application/json', 'X-App-ID': LUNOS_APP_ID}
    payload = {'model': 'openai/gpt-5', 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]}
    try:
        response = requests.post(LUNOS_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_response_data = response.json()
        json_string_content = ai_response_data['choices'][0]['message']['content']
        parsed_json = json.loads(json_string_content)
        print("Lunos.tech analysis and JSON parsing successful.")
        print(parsed_json)
        return parsed_json
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"ERROR: Failed to process or parse response from Lunos.tech. {e}")
        return None

def _verify_single_claim_with_unli(claim_text, api_key, app_id):
    system_prompt = "You are a meticulous and unbiased AI fact-checker. Your task is to evaluate a factual claim provided by the user. You must use your internal knowledge to determine if the claim is True, False, or Misleading. Your response must be a single, valid JSON object with three keys: 'claim', 'verdict', and 'explanation'. Provide a brief, neutral explanation for your verdict. Do not add any text outside the JSON object."
    user_prompt = f"Please fact-check this claim: {claim_text}"
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json', 'X-App-ID': app_id}
    payload = {'model': 'unli-auto', 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]} # IMPORTANT: Get model name from Unli docs
    try:
        response = requests.post(UNLI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_response_data = response.json()
        json_string_content = ai_response_data['choices'][0]['message']['content']
        return json.loads(json_string_content)
    except Exception as e:
        print(f"ERROR: Unli.dev failed to process claim '{claim_text}'. Reason: {e}")
        return {"claim": claim_text, "verdict": "Unverifiable", "explanation": "The fact-checking AI failed to process this claim."}

def check_claims_with_unli(claims_list):
    print(f"Fact-checking {len(claims_list)} claims one-by-one with Unli.dev...")
    verified_results = []
    for claim in claims_list:
        result = _verify_single_claim_with_unli(claim, UNLI_API_KEY, LUNOS_APP_ID) # Using LUNOS_APP_ID as placeholder for Unli's App ID
        verified_results.append(result)
    print("Unli.dev fact-checking loop complete.")
    return {"results": verified_results}

@app.route('/check-news', methods=['POST'])
def check_news_endpoint():
    # This main logic does not need to change at all, because we kept the output format of check_claims_with_unli the same!
    print("\n--- New Request Received at /check-news ---")
    data = request.get_json()
    if not data or 'content' not in data: return jsonify({'error': 'No content provided in the request.'}), 400
    news_content = data.get('content')
    lunos_result = extract_claims_with_lunos(news_content)
    if not lunos_result or 'claims' not in lunos_result or not lunos_result['claims']: return jsonify({'error': 'AI model failed to extract claims properly.'}), 500
    summary = lunos_result.get('summary', 'No summary available.')
    claims = lunos_result['claims']
    fact_check_results = check_claims_with_unli(claims)
    if not fact_check_results: return jsonify({'error': 'The fact-checking service failed to respond.'}), 500
    details = fact_check_results.get('results', [])
    verdicts = [result.get('verdict', 'Unverifiable').upper() for result in details]
    overall_verdict = 'VERIFIED'
    if 'FALSE' in verdicts: overall_verdict = 'CONTAINS FALSE INFORMATION'
    elif 'MISLEADING' in verdicts: overall_verdict = 'MISLEADING'
    final_response = {'summary': summary, 'overall_verdict': overall_verdict, 'details': details}
    print("--- Request Complete. Sending final response. ---")
    return jsonify(final_response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)