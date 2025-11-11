# save as 

import requests
import json
import re
import os
from tqdm import tqdm

LLM_API_URL = "http://localhost:11434/v1/chat/completions"

# IMPROVED BALANCED PROMPT - Less prescriptive, more effective
IMPROVED_PROMPT = """You are an expert argument analyst. Extract the core argumentative structure from this news article.

**Extract these four components:**

1. **THESIS**: The main claim or position the article advocates (1-2 statements)
2. **SUPPORTING CLAIMS**: Key reasons that support the thesis (2-5 claims)
3. **COUNTERARGUMENTS**: Opposing views or criticisms mentioned (0-3 if present)
4. **EVIDENCE**: Facts, statistics, expert quotes, or examples used (2-5 pieces)

**Guidelines:**
- Extract text verbatim or near-verbatim from the article
- Be thorough but focused on the strongest arguments
- If a category is not present in the text, return an empty list
- Capture both explicit and implicit counterarguments

**Return valid JSON only:**
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}

Article:
{text}

JSON:"""

def extract_argument_map_improved(text):
    """Extract arguments using improved balanced prompt"""
    prompt = IMPROVED_PROMPT.format(text=text[:3500])
    
    payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,  # Increased from 0.1 for better creativity
        "max_tokens": 1200,
    }
    
    try:
        resp = requests.post(LLM_API_URL, json=payload, timeout=90)
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
            arg_map[key] = [item.strip() for item in arg_map[key] if item and item.strip()]
        
        return arg_map
        
    except Exception as e:
        print(f"\n  ⚠️ Error: {e}")
        return None

def main():
    print("\n" + "="*70)
    print("IMPROVED PROMPT EXTRACTION (Version 2)")
    print("Balanced approach: Less prescriptive, higher temperature")
    print("="*70 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    baseline_path = os.path.join(script_dir, 'data', 'processed', 'reputable_news_dataset_cleaned.json')
    output_path = os.path.join(script_dir, 'data', 'processed', 'improved_model_dataset_v2.json')
    
    print(f"Loading baseline from: {baseline_path}")
    with open(baseline_path, 'r', encoding='utf-8') as f:
        baseline_articles = json.load(f)
    
    print(f"✓ Loaded {len(baseline_articles)} articles from baseline\n")
    
    improved_dataset = []
    failed = []
    
    print("Processing articles with improved prompt...")
    for article in tqdm(baseline_articles, desc="Extracting arguments"):
        source_id = article.get('source_id')
        text = article.get('text', '')
        
        if not text:
            tqdm.write(f"⚠️ {source_id}: No text available, skipping")
            failed.append(source_id)
            continue
        
        arg_map = extract_argument_map_improved(text)
        
        if not arg_map:
            tqdm.write(f"⚠️ {source_id}: Extraction failed, skipping")
            failed.append(source_id)
            continue
        
        improved_dataset.append({
            "source_id": source_id,
            "title": article.get('title', ''),
            "url": article.get('url', ''),
            "source": article.get('source', ''),
            "topic": article.get('topic', ''),
            "text": text,
            "argument_map": arg_map
        })
    
    print("\n\nSaving results...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(improved_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE (Version 2)")
    print(f"{'='*70}")
    print(f"✓ Successfully processed: {len(improved_dataset)} articles")
    print(f"✓ Failed/Skipped: {len(failed)} articles")
    if failed:
        print(f"  Failed IDs: {', '.join(failed)}")
    print(f"✓ Saved to: {output_path}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
