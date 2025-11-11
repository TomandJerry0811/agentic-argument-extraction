# Import the necessary libraries
from flask import Flask, request, jsonify, render_template
from functools import wraps
import requests
from bs4 import BeautifulSoup
import urllib.parse # Used to encode text for a URL
# Create a Flask web application
app = Flask(__name__)

# --- WHITELISTING LOGIC REMAINS THE SAME ---
ALLOWED_IPS = ['127.0.0.1', '192.168.1.15', '10.25.16.210', '172.16.39.12', '172.29.176.1', '192.168.0.183'] 

def ip_whitelist_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        if client_ip not in ALLOWED_IPS:
            print(f"Blocked request from un-authorized IP: {client_ip}")
            return jsonify({"error": f"Access denied for IP address: {client_ip}"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- NEW WEB SCRAPING FUNCTION ---
def scrape_google_for_context(query):
    """
    Fetch search results using Google Custom Search API instead of scraping HTML.
    """
    print(f"Querying Google Custom Search API for: '{query}'")
    API_KEY = "AIzaSyDWQ40EjEi_4DAiy4hn4mo0n0g-25NX9gY"  # <-- paste your API key here
    CX = "65d879a5b90884259"         # <-- your CSE ID from the screenshot

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CX,
        "num": 5                     # number of results to fetch (max 10)
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract snippets from results
        if "items" in data:
            snippets = [item.get("snippet", "") for item in data["items"]]
            context = " ".join(snippets)
            print(f"Found context: {context[:200]}...")
            return context
        else:
            print("No search results found.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error querying Google Custom Search API: {e}")
        return None

# --- API AND MAIN APP LOGIC ---
AI_API_URL = "http://localhost:11434/v1/chat/completions"

@app.route('/', methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
@ip_whitelist_required
def ask_model():
    user_data = request.get_json()
    if not user_data or 'question' not in user_data:
        return jsonify({"error": "Invalid request. Please provide a 'question'."}), 400
    
    user_question = user_data['question']
    print(f"Received question from allowed IP: {request.remote_addr}")

    # --- RAG WORKFLOW STARTS HERE ---
    
    # 1. RETRIEVE: Scrape the web for real-time information
    context = scrape_google_for_context(user_question)
    
    # If we found context, build the special prompt. Otherwise, just use the original question.
    if context:
        # 2. AUGMENT: Create the new prompt for the LLM
        augmented_prompt = f"""Context:
        \"\"\"
        {context}
        \"\"\"
        Based ONLY on the context provided above, please answer the following question: {user_question}
        """
        final_content_for_llm = augmented_prompt
    else:
        # If scraping fails, proceed without the extra context
        print("Proceeding without web context.")
        final_content_for_llm = user_question

    # --- RAG WORKFLOW ENDS HERE ---

    api_payload = {
        "model": "gemma3",
        "messages": [{"role": "user", "content": final_content_for_llm}], # Use the final prompt
        "temperature": 0.7,
        "max_tokens": 512,
    }

    try:
        response = requests.post(AI_API_URL, json=api_payload)
        response.raise_for_status()
        ai_response_data = response.json()
        answer = ai_response_data['choices'][0]['message']['content']
        cleaned_answer = answer.replace("\n", "<br>")
        return jsonify({"answer": cleaned_answer})

        # return jsonify({"answer": answer})
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to AI server: {e}")
        return jsonify({"error": "Could not connect to the local AI model."}), 500
    except (KeyError, IndexError) as e:
        print(f"Error parsing AI response: {e}")
        return jsonify({"error": "Received an unexpected response format."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)