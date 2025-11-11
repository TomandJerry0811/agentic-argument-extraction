import requests
import json
import re
import os
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# ============================================================================
# ALL STATIC PROMPTS (7 prompts) - UNCHANGED
# ============================================================================

BASELINE_PROMPT = """Extract thesis, supporting claims, counterclaims, and evidence from this article. 
Return ONLY a valid JSON with keys: thesis, supporting_claims, counterarguments, evidence (all lists).

Article:
{text}"""

FEW_SHOT_PROMPT = """You are an expert argument analyst. I will show you examples of how to extract arguments, then you will do the same for a new article.

**Example 1:**
Article: "Electric vehicles are the future. They produce zero emissions and reduce oil dependency. However, critics worry about battery disposal."

Output:
{{
  "thesis": ["Electric vehicles are the future of transportation"],
  "supporting_claims": ["They produce zero emissions", "Reduce oil dependency"],
  "counterarguments": ["Critics worry about battery disposal"],
  "evidence": []
}}

**Example 2:**
Article: "The new policy will create jobs, according to economists. Studies show 50,000 new positions. But some fear increased costs."

Output:
{{
  "thesis": ["The new policy will create jobs"],
  "supporting_claims": ["According to economists, it will create employment"],
  "counterarguments": ["Some fear increased costs"],
  "evidence": ["Studies show 50,000 new positions"]
}}

**Now analyze this article:**

{text}

Return JSON only:
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}"""

CHAIN_OF_THOUGHT_PROMPT = """You are an expert argument analyst. Analyze this article step-by-step:

**Step 1: Read and identify the main debate**
First, determine what issue or question the article addresses.

**Step 2: Find the thesis**
What is the main claim or position the article advocates? (1-2 statements)

**Step 3: Extract supporting claims**
What reasons or arguments support the thesis? (2-5 claims)

**Step 4: Look for counterarguments**
Are there opposing views, criticisms, or alternative perspectives mentioned? Look for phrases like "critics argue", "however", "on the other hand". (0-3 if present)

**Step 5: Identify evidence**
What facts, statistics, quotes, or examples back up the claims? (2-5 pieces)

**Article:**
{text}

**Now provide your analysis as JSON:**
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}"""

ROLE_BASED_PROMPT = """You are a professional debate coach and argument analyst with 15 years of experience in identifying logical structures in persuasive texts.

Your expertise includes:
- Identifying implicit arguments and unstated assumptions
- Recognizing subtle counterarguments and opposing viewpoints
- Distinguishing between claims and evidence
- Extracting verbatim quotes and factual support

**Your task:** Extract the argument structure from this news article.

**What to extract:**

**THESIS** - The main position or claim (1-2 statements)
- Look for: Overall message, main point, primary argument

**SUPPORTING CLAIMS** - Reasons that support the thesis (2-5 claims)  
- Look for: Because statements, justifications, rationales

**COUNTERARGUMENTS** - Opposing views mentioned (0-3 if present)
- Look for: "Critics say", "However", "Some argue", "Opposition claims", skeptical voices

**EVIDENCE** - Facts, data, quotes, examples (2-5 pieces)
- Look for: Statistics, study results, expert quotes, specific examples, data points

**Important:** Extract text as it appears in the article. Be thorough but precise.

**Article:**
{text}

**Return JSON only:**
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}"""

CONTRASTIVE_PROMPT = """You are an expert argument analyst. Extract arguments following these guidelines:

**DO:**
✓ Extract text verbatim or nearly verbatim from the article
✓ Look carefully for opposing views (even if subtle)
✓ Include all types of evidence: numbers, quotes, studies, examples
✓ Be thorough and capture ALL relevant arguments

**DON'T:**
✗ Infer arguments not explicitly stated
✗ Paraphrase excessively
✗ Miss subtle counterarguments hidden in phrases like "critics argue", "some worry"
✗ Skip over evidence buried in the text

**Extract:**

1. **THESIS**: Main claim/position (1-2 statements)
2. **SUPPORTING CLAIMS**: Reasons supporting thesis (2-5 claims)
3. **COUNTERARGUMENTS**: Opposing views mentioned (0-3 if present)
4. **EVIDENCE**: Facts, stats, quotes, examples (2-5 pieces)

**Article:**
{text}

**JSON output:**
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}"""

STRUCTURED_OUTPUT_PROMPT = """<task>
Extract argument structure from news article
</task>

<role>
Expert argument analyst
</role>

<instructions>
1. Read article to identify the debate/issue
2. Extract THESIS: main position (1-2 statements)
3. Extract SUPPORTING_CLAIMS: reasons for thesis (2-5 items)
4. Extract COUNTERARGUMENTS: opposing views mentioned (0-3 items)
   - Pay special attention to: "critics", "however", "some argue", "opponents"
5. Extract EVIDENCE: facts, stats, quotes, examples (2-5 items)
</instructions>

<extraction_rules>
- Use verbatim or near-verbatim text from article
- Be comprehensive, not selective
- If category is absent, return empty list
- Preserve original meaning and tone
</extraction_rules>

<output_format>
Valid JSON with keys: thesis, supporting_claims, counterarguments, evidence
All values must be lists of strings
</output_format>

<article>
{text}
</article>

<output>
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}
</output>"""

RECURSIVE_PROMPT = """You are an expert argument analyst. Extract arguments from this article using a two-pass approach:

**PASS 1: Initial extraction**
First, extract all arguments you can find.

**PASS 2: Critical review**  
Review your Pass 1 extraction and ask:
- Did I miss any counterarguments? Look for "critics", "however", "some say"
- Did I miss any evidence? Look for statistics, quotes, studies
- Are my thesis statements too broad or too narrow?
- Did I capture enough supporting claims?

**PASS 3: Final refined output**
Provide your improved extraction incorporating insights from your review.

**Categories to extract:**
- THESIS: Main position (1-2 statements)
- SUPPORTING CLAIMS: Reasons supporting thesis (2-5)
- COUNTERARGUMENTS: Opposing views (0-3 if present)
- EVIDENCE: Facts, stats, quotes, examples (2-5)

**Article:**
{text}

**Provide your final refined extraction as JSON:**
{{"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}}"""

STATIC_PROMPTS = {
    "baseline": {"prompt": BASELINE_PROMPT, "temperature": 0.2},
    "few_shot": {"prompt": FEW_SHOT_PROMPT, "temperature": 0.2},
    "chain_of_thought": {"prompt": CHAIN_OF_THOUGHT_PROMPT, "temperature": 0.3},
    "role_based": {"prompt": ROLE_BASED_PROMPT, "temperature": 0.2},
    "contrastive": {"prompt": CONTRASTIVE_PROMPT, "temperature": 0.2},
    "structured_output": {"prompt": STRUCTURED_OUTPUT_PROMPT, "temperature": 0.1},
    "recursive": {"prompt": RECURSIVE_PROMPT, "temperature": 0.3}
}

MODELS = ["llama3.1", "llama3.2", "gemma2"]

# ============================================================================
# FIXED EXTRACTION FUNCTION
# ============================================================================

def extract_arguments(text, prompt_template, model_name, temperature=0.2):
    """Extract arguments using specified prompt and model - WITH FIX"""
    prompt = prompt_template.format(text=text[:3500])
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1500,
    }
    
    try:
        resp = requests.post("http://localhost:11434/v1/chat/completions", json=payload, timeout=90)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if not match:
            return None
        
        arg_map = json.loads(match.group(0))
        
        # FIX: Handle nested structures and convert everything to strings
        for key in ["thesis", "supporting_claims", "counterarguments", "evidence"]:
            if key not in arg_map:
                arg_map[key] = []
            elif not isinstance(arg_map[key], list):
                arg_map[key] = [str(arg_map[key])]
            
            # NEW: Flatten nested structures and convert all items to strings
            cleaned_items = []
            for item in arg_map[key]:
                if isinstance(item, dict):
                    # If item is a dict, extract values and join them
                    cleaned_items.append(' '.join(str(v) for v in item.values() if v))
                elif isinstance(item, list):
                    # If item is a list, join its elements
                    cleaned_items.append(' '.join(str(i) for i in item if i))
                else:
                    # If item is already a string or other type
                    cleaned_items.append(str(item))
            
            # Clean empty strings and whitespace
            arg_map[key] = [item.strip() for item in cleaned_items if item and str(item).strip()]
        
        return arg_map
        
    except Exception as e:
        print(f" ✗ ({str(e)[:30]})")
        return None

# ============================================================================
# SCRAPING - UNCHANGED
# ============================================================================

def scrape_article(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        title = soup.find('title').get_text() if soup.find('title') else ''
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs[:15]])
        if len(content) < 200:
            return None, None
        return title, content
    except:
        return None, None

# ============================================================================
# MAIN - UNCHANGED
# ============================================================================

def main():
    print("\n" + "="*70)
    print("COMPREHENSIVE STATIC EXTRACTION SYSTEM")
    print("7 Prompts × 3 Models = 21 Different Configurations")
    print("="*70 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gold_path = os.path.join(script_dir, 'data', 'gold_standard', 'human_annotated_ground_truth_FIXED.json')
    
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    
    print(f"✓ Loaded {len(gold_standard)} articles\n")
    
    all_results = {model: {prompt: [] for prompt in STATIC_PROMPTS.keys()} for model in MODELS}
    
    for idx, article in enumerate(gold_standard):
        source_id = article['source_id']
        url = article.get('url', '')
        title = article.get('title', '')
        topic = article.get('topic', '')
        source = article.get('source', '')
        
        print(f"\n[{idx+1}/{len(gold_standard)}] {source_id}")
        print(f"   Title: {title[:60]}...")
        
        if not url:
            continue
        
        scraped_title, text = scrape_article(url)
        if not text:
            print(f"   ❌ Scraping failed")
            continue
        
        full_text = f"{title}\n{text}"
        
        for model_name in MODELS:
            print(f"   🔄 {model_name}...")
            
            for prompt_name, config in STATIC_PROMPTS.items():
                print(f"      - {prompt_name}...", end="", flush=True)
                
                arg_map = extract_arguments(
                    full_text,
                    config["prompt"],
                    model_name,
                    temperature=config["temperature"]
                )
                
                if arg_map:
                    all_results[model_name][prompt_name].append({
                        "source_id": source_id,
                        "title": title,
                        "url": url,
                        "source": source,
                        "topic": topic,
                        "text": full_text,
                        "argument_map": arg_map
                    })
                    print(" ✓")
                else:
                    print(" ✗")
                
                time.sleep(0.5)
        
        print(f"   ✅ Completed")
    
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print("="*70)
    
    output_dir = os.path.join(script_dir, 'data', 'processed', 'static_models')
    os.makedirs(output_dir, exist_ok=True)
    
    for model_name in MODELS:
        for prompt_name, results in all_results[model_name].items():
            filename = f'{model_name}_{prompt_name}.json'
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"✓ {model_name} + {prompt_name}: {len(results)} articles")
    
    print(f"\n✅ ALL STATIC CONFIGURATIONS COMPLETED\n")

if __name__ == "__main__":
    main()
