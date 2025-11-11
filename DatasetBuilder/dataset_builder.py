import requests
import json
import time
import re
from bs4 import BeautifulSoup
from ddgs.ddgs import DDGS

LLM_API_URL = "http://localhost:11434/v1/chat/completions"

# Single list of reputable sources
REPUTABLE_SOURCES = [
    "bbc.com",
    "theguardian.com",
    "reuters.com",
    "apnews.com",
    "npr.org"
]

TOPICS = [
    "climate change policy",
    "artificial intelligence regulation",
    "electric vehicles future",
    "remote work debate",
    "social media regulation",
    "healthcare reform",
    "cryptocurrency regulation",
    "immigration policy",
    "education reform",
    "renewable energy"
]

def fetch_articles(topic, source, max_articles=2):
    """Fetch articles from specific source"""
    articles = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        query = f"{topic} site:{source}"
        
        with DDGS() as ddgs:
            results = list(ddgs.news(query=query, max_results=max_articles))
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                paragraphs = soup.find_all('p')
                content = " ".join([p.get_text() for p in paragraphs[:15]])
                
                if len(content) > 300:
                    articles.append({
                        "title": title,
                        "url": url,
                        "content": content,
                        "source": source,
                        "topic": topic
                    })
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    Skip {url}: {e}")
                continue
    
    except Exception as e:
        print(f"  Search error: {e}")
    
    return articles

def extract_argument_map(text):
    """Extract arguments using LLM"""
    prompt = (
        "Extract thesis, supporting claims, counterclaims, and evidence from this article. "
        "Return ONLY a valid JSON with keys: thesis, supporting_claims, counterarguments, evidence (all lists).\n\n"
        "Article:\n" + text[:1500]
    )
    
    payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    
    try:
        resp = requests.post(LLM_API_URL, json=payload, timeout=60)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if not match:
            return None
        
        arg_map = json.loads(match.group(0))
        
        for key in ["thesis", "supporting_claims", "counterarguments", "evidence"]:
            if key not in arg_map:
                arg_map[key] = []
            elif not isinstance(arg_map[key], list):
                arg_map[key] = [str(arg_map[key])]
        
        return arg_map
        
    except Exception as e:
        return None

def main():
    print("Building single dataset from reputable sources...\n")
    dataset = []
    
    for topic in TOPICS:
        print(f"\nTopic: {topic}")
        for source in REPUTABLE_SOURCES:
            print(f"  Source: {source}...", end="")
            articles = fetch_articles(topic, source, max_articles=2)
            print(f" {len(articles)} articles")
            
            for article in articles:
                text = f"{article['title']}\n{article['content']}"
                arg_map = extract_argument_map(text)
                
                if arg_map:
                    dataset.append({
                        "source_id": f"article_{len(dataset)+1}",
                        "title": article['title'],
                        "url": article['url'],
                        "source": article['source'],
                        "topic": article['topic'],
                        "text": text[:500],
                        "argument_map": arg_map
                    })
                
                time.sleep(1)
    
    # Save single dataset
    with open('data/processed/reputable_news_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'='*60}")
    print(f"✓ COMPLETE! Saved {len(dataset)} articles")
    print(f"✓ File: data/processed/reputable_news_dataset.json")
    print(f"{'='*60}\n")
    
    # Show distribution
    for source in REPUTABLE_SOURCES:
        count = len([a for a in dataset if a['source'] == source])
        print(f"  {source}: {count} articles")

if __name__ == "__main__":
    main()
