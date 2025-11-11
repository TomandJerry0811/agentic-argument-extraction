import requests
import json
import re
import os
from tqdm import tqdm

LLM_API_URL = "http://localhost:11434/v1/chat/completions"

# Enhanced prompt for better extraction
ENHANCED_PROMPT = """You are an expert argument analyst specializing in identifying logical structures in persuasive texts. Your task is to extract arguments from news articles with precision and completeness.

**Instructions:**
1. Read the article carefully to understand the main debate or issue
2. Identify ONLY arguments explicitly stated in the text (no inference)
3. Extract complete sentences or phrases that preserve original meaning
4. Be thorough - capture ALL relevant arguments, not just the most prominent ones

**Definitions:**
- **THESIS**: The main argument, claim, or position the article advocates. This is the central point the author wants readers to believe or accept. (Usually 1-2 statements)
- **SUPPORTING CLAIMS**: Specific reasons, assertions, or sub-arguments that directly support the thesis. These explain WHY the thesis should be accepted. (Usually 2-5 claims)
- **COUNTERARGUMENTS**: Opposing viewpoints, criticisms, or alternative perspectives mentioned in the article. These challenge or contradict the thesis. Include skeptical voices, critics, or dissenting opinions. (Usually 1-3 counterarguments)
- **EVIDENCE**: Concrete facts, statistics, quotes from experts, research findings, or real-world examples that back up the claims. This includes data, studies, testimonials, and factual observations. (Usually 2-5 pieces of evidence)

**Important Guidelines:**
✓ Extract verbatim or near-verbatim text from the article
✓ Capture implicit counterarguments (e.g., "Some critics argue...", "However, opponents claim...")
✓ Include ALL types of evidence: statistics, expert quotes, examples, studies
✓ If a category has no clear examples in the text, return an empty list []
✓ Preserve the original tone and meaning - do not paraphrase excessively

**Output Format:**
Return ONLY a valid JSON object with exactly these four keys (no additional text or explanation):
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}

Article:
{text}

JSON Output:"""

def extract_argument_map_enhanced(text):
    """Extract arguments using enhanced model"""
    prompt = ENHANCED_PROMPT.format(text=text[:3500])
    
    payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1500,
    }
    
    try:
        resp = requests.post(LLM_API_URL, json=payload, timeout=90)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        # Extract JSON from response
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if not match:
            return None
        
        arg_map = json.loads(match.group(0))
        
        # Ensure all keys exist and are lists
        for key in ["thesis", "supporting_claims", "counterarguments", "evidence"]:
            if key not in arg_map:
                arg_map[key] = []
            elif not isinstance(arg_map[key], list):
                arg_map[key] = [str(arg_map[key])]
            # Clean empty strings
            arg_map[key] = [item.strip() for item in arg_map[key] if item and item.strip()]
        
        return arg_map
        
    except Exception as e:
        print(f"\n  ⚠️ Error: {e}")
        return None

def main():
    print("\n" + "="*70)
    print("ENHANCED MODEL EXTRACTION")
    print("Using existing text from baseline for fair comparison")
    print("="*70 + "\n")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build paths relative to script location
    baseline_path = os.path.join(script_dir, 'data', 'processed', 'reputable_news_dataset_cleaned.json')
    output_path = os.path.join(script_dir, 'data', 'processed', 'enhanced_model_dataset.json')
    
    # Load baseline JSON
    print(f"Loading baseline from: {baseline_path}")
    with open(baseline_path, 'r', encoding='utf-8') as f:
        baseline_articles = json.load(f)
    
    print(f"✓ Loaded {len(baseline_articles)} articles from baseline\n")
    
    enhanced_dataset = []
    failed = []
    
    print("Processing articles with enhanced model...")
    for article in tqdm(baseline_articles, desc="Extracting arguments"):
        source_id = article.get('source_id')
        text = article.get('text', '')
        
        if not text:
            tqdm.write(f"⚠️ {source_id}: No text available, skipping")
            failed.append(source_id)
            continue
        
        # Extract with enhanced model using SAME text as baseline
        arg_map = extract_argument_map_enhanced(text)
        
        if not arg_map:
            tqdm.write(f"⚠️ {source_id}: Extraction failed, skipping")
            failed.append(source_id)
            continue
        
        # Keep all original fields, only update argument_map
        enhanced_dataset.append({
            "source_id": source_id,
            "title": article.get('title', ''),
            "url": article.get('url', ''),
            "source": article.get('source', ''),
            "topic": article.get('topic', ''),
            "text": text,
            "argument_map": arg_map  # ONLY this field changes
        })
    
    # Save results
    print("\n\nSaving results...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Successfully processed: {len(enhanced_dataset)} articles")
    print(f"✓ Failed/Skipped: {len(failed)} articles")
    if failed:
        print(f"  Failed IDs: {', '.join(failed)}")
    print(f"✓ Saved to: {output_path}")
    print(f"{'='*70}\n")
    
    print("Next step: Run compare_models.py to see the comparison!\n")

if __name__ == "__main__":
    main()
