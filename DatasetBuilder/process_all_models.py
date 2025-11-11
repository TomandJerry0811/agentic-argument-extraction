import requests
import json
import re
import os
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

LLM_API_URL = "http://localhost:11434/v1/chat/completions"

# ============================================================================
# ALL PROMPTS (BASELINE + 6 ADVANCED)
# ============================================================================

# BASELINE PROMPT (Simple)
BASELINE_PROMPT = """Extract thesis, supporting claims, counterclaims, and evidence from this article. 
Return ONLY a valid JSON with keys: thesis, supporting_claims, counterarguments, evidence (all lists).

Article:
{text}"""

# 1. FEW-SHOT PROMPT
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

# 2. CHAIN-OF-THOUGHT PROMPT
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

# 3. ROLE-BASED PROMPT
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

# 4. CONTRASTIVE PROMPT
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

# 5. STRUCTURED-OUTPUT PROMPT
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

# 6. RECURSIVE PROMPT
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

# ============================================================================
# PROMPT CONFIGURATIONS
# ============================================================================

PROMPTS = {
    "baseline": {"prompt": BASELINE_PROMPT, "temperature": 0.2},
    "few_shot": {"prompt": FEW_SHOT_PROMPT, "temperature": 0.2},
    "chain_of_thought": {"prompt": CHAIN_OF_THOUGHT_PROMPT, "temperature": 0.3},
    "role_based": {"prompt": ROLE_BASED_PROMPT, "temperature": 0.2},
    "contrastive": {"prompt": CONTRASTIVE_PROMPT, "temperature": 0.2},
    "structured_output": {"prompt": STRUCTURED_OUTPUT_PROMPT, "temperature": 0.1},
    "recursive": {"prompt": RECURSIVE_PROMPT, "temperature": 0.3}
}

# ============================================================================
# SCRAPING FUNCTION
# ============================================================================

def scrape_article(url):
    """Scrape article content from URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
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
        
    except Exception as e:
        return None, None

# ============================================================================
# EXTRACTION FUNCTION
# ============================================================================

def extract_arguments(text, prompt_template, temperature=0.2):
    """Extract arguments using specified prompt"""
    prompt = prompt_template.format(text=text[:3500])
    
    payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1500,
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
        return None

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    print("\n" + "="*70)
    print("PROCESSING ALL 7 MODELS ON GOLD STANDARD ARTICLES")
    print("Baseline + 6 Advanced Prompts")
    print("="*70 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load gold standard
    gold_path = os.path.join(script_dir, 'data', 'gold_standard', 'human_annotated_ground_truth_FIXED.json')
    print(f"Loading gold standard from: {gold_path}")
    
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    
    print(f"✓ Found {len(gold_standard)} articles in gold standard\n")
    
    # Prepare results containers for all models
    results = {name: [] for name in PROMPTS.keys()}
    
    # Process each article
    for idx, gold_article in enumerate(gold_standard):
        source_id = gold_article['source_id']
        url = gold_article.get('url', '')
        title = gold_article.get('title', '')
        topic = gold_article.get('topic', '')
        source = gold_article.get('source', '')
        
        print(f"\n[{idx+1}/{len(gold_standard)}] {source_id}")
        print(f"   Title: {title[:60]}...")
        
        if not url:
            print(f"   ❌ No URL, skipping")
            continue
        
        # Scrape article
        print(f"   📥 Scraping...")
        scraped_title, text = scrape_article(url)
        
        if not text:
            print(f"   ❌ Scraping failed, skipping")
            continue
        
        full_text = f"{title}\n{text}"
        print(f"   ✓ Scraped {len(text)} chars")
        
        # Process with ALL prompts
        for prompt_name, config in PROMPTS.items():
            print(f"   🔄 {prompt_name.replace('_', ' ').title()}...")
            
            arg_map = extract_arguments(
                full_text, 
                config["prompt"], 
                temperature=config["temperature"]
            )
            
            if arg_map:
                results[prompt_name].append({
                    "source_id": source_id,
                    "title": title,
                    "url": url,
                    "source": source,
                    "topic": topic,
                    "text": full_text,
                    "argument_map": arg_map
                })
                print(f"   ✓ {prompt_name} done")
            else:
                print(f"   ⚠️ {prompt_name} failed")
            
            time.sleep(1)  # Rate limiting
        
        print(f"   ✅ All models completed")
    
    # Save all results
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print("="*70)
    
    output_dir = os.path.join(script_dir, 'data', 'processed')
    
    for prompt_name, prompt_results in results.items():
        output_file = os.path.join(output_dir, f'{prompt_name}_model.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(prompt_results, f, indent=2, ensure_ascii=False)
        print(f"✓ {prompt_name.replace('_', ' ').title()}: {len(prompt_results)} articles → {prompt_name}_model.json")
    
    print(f"\n✅ ALL DONE! Now run compare_all_models.py to see results.\n")

if __name__ == "__main__":
    main()
