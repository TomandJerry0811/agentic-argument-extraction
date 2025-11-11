import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import requests
from bs4 import BeautifulSoup
from ddgs.ddgs import DDGS

# --- Flask app setup ---
app = Flask(__name__)
CORS(app,
     origins="*",
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# --- IP Whitelisting ---
ALLOWED_IPS = ['127.0.0.1', '::1', '192.168.1.15', '10.25.16.210', '172.16.39.12', '172.29.176.1', '192.168.0.183']

def ip_whitelist_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        if client_ip not in ALLOWED_IPS:
            print(f"Blocked request from un-authorized IP: {client_ip}")
            return jsonify({"error": f"Access denied for IP address: {client_ip}"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Web scraping function ---
def get_web_context_for_query(query, max_articles=3):
    print(f"Searching and scraping web for: '{query}'")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36"
    }
    combined_context = ""
    sources = []
    skipped_urls = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query=query, max_results=max_articles))

        if not results:
            print("No news articles found for the query.")
            return None, None, None

        for i, result in enumerate(results):
            url = result['url']
            print(f"Scraping URL ({i+1}/{max_articles}): {url}")
            try:
                response = requests.get(url, headers=headers, timeout=10)  # ⏱ 10s timeout
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'lxml')
                title = soup.find('title').get_text() if soup.find('title') else ''
                paragraphs = soup.find_all('p')
                article_text = " ".join([p.get_text() for p in paragraphs])

                combined_context += (
                    f"--- START OF SOURCE {i+1} ---\n"
                    f"URL: {url}\nTITLE: {title}\nCONTENT: {article_text}\n"
                    f"--- END OF SOURCE {i+1} ---\n\n"
                )
                sources.append(url)

            except requests.exceptions.Timeout:
                print(f"⏳ Skipped {url}: request timed out (10s).")
                skipped_urls.append(url)
                continue
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not scrape {url}: {e}")
                skipped_urls.append(url)
                continue

        return combined_context if combined_context else None, sources, skipped_urls
    except Exception as e:
        print(f"An error occurred during the search process: {e}")
        return None, None, None

# --- API and main logic ---
AI_API_URL = "http://localhost:11434/v1/chat/completions"

@app.route('/', methods=['GET'])
def homepage():
    return "<h1>Flask API Server is Running!</h1><p>Send a POST request to /ask to interact with the LLM.</p>"

@app.route('/ask', methods=['POST'])
@ip_whitelist_required
def ask_model():
    user_data = request.get_json()
    if not user_data or 'question' not in user_data:
        return jsonify({"error": "Invalid request. Please provide a 'question'."}), 400

    user_question = user_data['question']
    print(f"Received question from allowed IP: {request.remote_addr}")

    context, sources, skipped_urls = get_web_context_for_query(user_question)

    if not context:
        print("Scraping failed or no context found. Aborting request.")
        return jsonify({"error": "Could not find relevant online information for your query. Please try a different topic."}), 400

    augmented_prompt = f"""You are an expert logician and research analyst named 'The Argument Cartographer'. 
Your task is to deconstruct the provided text into a structured argument map.

Your output MUST be a single, clean JSON object. Do not add any conversational text, explanations, 
or markdown formatting like ```json before or after the JSON.

The JSON object must have a 'title' key and an 'elements' key. 
The 'elements' key must contain a list of objects. Each element object in the list must have:
- "id": A unique string identifier (e.g., "thesis-1", "claim-1", "evidence-1a").
- "type": One of: "Thesis", "Supporting Claim", "Evidence", "Counterclaim", or "Logical Fallacy".
- "parentId": The "id" of the element it supports. For the "Thesis", this should be null.
- "content": A concise summary of the argument component. You MUST include the citation (e.g., [Source 1]).
- "sourceText": The exact quote from the original text that this element is based on.

--- TEXT TO ANALYZE ---
{context}
--- END OF TEXT ---

Now, analyze the text about "{user_question}" and provide the JSON output.
"""

    api_payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": augmented_prompt}],
        "temperature": 0.2,
        "max_tokens": 2048,
    }

    try:
        response = requests.post(AI_API_URL, json=api_payload, timeout=360)  # ⏱ 180s timeout
        response.raise_for_status()
        ai_response_data = response.json()

        answer_content_string = ai_response_data['choices'][0]['message']['content']

        # Safe JSON parsing
        import re
        import json
        match = re.search(r"\{.*\}", answer_content_string, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in AI response")
        argument_map_dict = json.loads(match.group(0))

        return jsonify({
            "data": answer_content_string,
            "argument_map": argument_map_dict,
            "sources": sources,
            "skipped_urls": skipped_urls
        })

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to AI server: {e}")
        return jsonify({"error": "Could not connect to the local AI model."}), 500
    except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
        print(f"Error parsing AI response: {e}")
        return jsonify({
            "error": "Failed to parse the response from the AI.",
            "raw_response": answer_content_string
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
