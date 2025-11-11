# Import the necessary libraries
from flask import Flask, request, jsonify
from functools import wraps
import requests
from newsapi import NewsApiClient # New import for NewsAPI

# Create a Flask web application
app = Flask(__name__)

# --- NEW: ADD YOUR NEWSAPI.ORG API KEY HERE ---
# For a real project, you should set this as an environment variable
NEWS_API_KEY = "30a62c33eacf4c63903261145a5f64c6"
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# --- WHITELISTING LOGIC REMAINS THE SAME ---
ALLOWED_IPS = ['127.0.0.1', '192.168.1.15', '10.25.16.210', '172.16.39.12', '172.29.176.1', '192.168.0.183'] 

def ip_whitelist_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        if client_ip not in ALLOWED_IPS:
            return jsonify({"error": f"Access denied for IP address: {client_ip}"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- UPDATED WEB CONTEXT FUNCTION USING NEWSAPI ---
def get_web_context_for_query(query, max_articles=5):
    """
    Uses the NewsAPI to get the top recent articles for a query.
    """
    print(f"Searching NewsAPI for: '{query}'")
    try:
        # Fetch the top 5 most relevant English articles
        top_headlines = newsapi.get_everything(q=query,
                                               language='en',
                                               sort_by='relevancy',
                                               page_size=max_articles)
        
        articles = top_headlines.get('articles', [])
        
        if not articles:
            print("No news articles found for the query.")
            return None, None

        combined_context = ""
        sources = []

        # Use the content snippets provided by the API for reliability
        for i, article in enumerate(articles):
            content = article.get('content') or article.get('description', '')
            url = article.get('url')
            
            if content and url:
                combined_context += f"[Source {i+1}: {url}]\n{content}\n\n"
                sources.append(url)
        
        print(f"Found {len(sources)} articles from NewsAPI.")
        return combined_context, sources

    except Exception as e:
        print(f"An error occurred with the NewsAPI: {e}")
        return None, None

# --- API AND MAIN APP LOGIC ---
AI_API_URL = "http://localhost:11440/v1/chat/completions"

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
    
    # RETRIEVE: Get context and sources from NewsAPI
    context, sources = get_web_context_for_query(user_question)
    
    if not context:
        return jsonify({"error": "Could not find relevant online information for your query."}), 400
    
    # AUGMENT: Create the new prompt for the LLM
    augmented_prompt = f"""You are a research assistant for the Argument Cartographer. Your task is to generate a structured argument map based ONLY on the context provided below. For every claim and piece of evidence you extract, you MUST cite the source number from the list of sources (e.g., [Source 1], [Source 2]).

    Context:
    \"\"\"
    {context}
    \"\"\"
    
    Now, generate the argument map for the topic: "{user_question}"
    """

    api_payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": augmented_prompt}],
        "temperature": 0.5,
        "max_tokens": 1024,
    }

    try:
        response = requests.post(AI_API_URL, json=api_payload)
        response.raise_for_status()
        ai_response_data = response.json()
        answer = ai_response_data['choices'][0]['message']['content']
        return jsonify({"answer": answer, "sources": sources})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Could not connect to the local AI model."}), 500
    except (KeyError, IndexError) as e:
        return jsonify({"error": "Received an unexpected response format."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)