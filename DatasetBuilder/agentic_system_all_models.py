import requests
import json
import re
import os
from bs4 import BeautifulSoup
import time
from comprehensive_extraction_system import STATIC_PROMPTS, scrape_article

MODELS = ["llama3.1", "llama3.2", "gemma2"]

class ReActAgentMultiModel:
    def __init__(self, model_name):
        self.model_name = model_name
        self.llm_url = "http://localhost:11434/v1/chat/completions"
        self.decision_log = []
        self.available_strategies = list(STATIC_PROMPTS.keys())
    
    def _analyze_article(self, text):
        counter_keywords = ["however", "but", "critics", "opponents", "some argue"]
        evidence_keywords = ["study", "research", "data", "statistics", "survey"]
        has_counters = any(kw in text.lower() for kw in counter_keywords)
        has_evidence = any(kw in text.lower() for kw in evidence_keywords)
        word_count = len(text.split())
        
        if word_count > 2000 and has_counters and has_evidence:
            return "highly_complex"
        elif has_counters and has_evidence:
            return "complex"
        elif has_counters:
            return "debate_heavy"
        elif has_evidence:
            return "evidence_heavy"
        else:
            return "simple"
    
    def _decide_strategy(self, text, article_type):
        reasoning_prompt = f"""Choose the BEST extraction strategy for this article.

Article Type: {article_type}
Preview: {text[:300]}...

Options: baseline, few_shot, chain_of_thought, role_based, contrastive, structured_output, recursive

Respond with ONLY the strategy name."""

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": reasoning_prompt}],
            "temperature": 0.1,
            "max_tokens": 50,
        }
        
        try:
            resp = requests.post(self.llm_url, json=payload, timeout=30)
            decision = resp.json()["choices"][0]["message"]["content"].strip().lower()
            
            for strategy in self.available_strategies:
                if strategy in decision:
                    return strategy
            
            return self._heuristic_fallback(article_type)
        except:
            return self._heuristic_fallback(article_type)
    
    def _heuristic_fallback(self, article_type):
        mapping = {
            "highly_complex": "recursive",
            "complex": "chain_of_thought",
            "debate_heavy": "few_shot",
            "evidence_heavy": "role_based",
            "simple": "baseline"
        }
        return mapping.get(article_type, "baseline")
    
    def _extract(self, text, strategy):
        config = STATIC_PROMPTS[strategy]
        prompt = config["prompt"].format(text=text[:3500])
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": 1500,
        }
        
        try:
            resp = requests.post(self.llm_url, json=payload, timeout=90)
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
                
                cleaned_items = []
                for item in arg_map[key]:
                    if isinstance(item, dict):
                        cleaned_items.append(' '.join(str(v) for v in item.values() if v))
                    elif isinstance(item, list):
                        cleaned_items.append(' '.join(str(i) for i in item if i))
                    else:
                        cleaned_items.append(str(item))
                
                arg_map[key] = [item.strip() for item in cleaned_items if item and str(item).strip()]
            
            return arg_map
        except:
            return None
    
    def _validate(self, extraction):
        if not extraction:
            return 0.0
        has_thesis = len(extraction.get("thesis", [])) > 0
        has_claims = len(extraction.get("supporting_claims", [])) >= 2
        has_evidence = len(extraction.get("evidence", [])) > 0
        completeness = (has_thesis * 0.4 + has_claims * 0.4 + has_evidence * 0.2)
        has_counters = len(extraction.get("counterarguments", [])) > 0
        if has_counters:
            completeness += 0.1
        return min(1.0, completeness)
    
    def process(self, text, source_id, max_retries=2):
        article_type = self._analyze_article(text)
        
        for attempt in range(max_retries):
            strategy = self._decide_strategy(text, article_type)
            result = self._extract(text, strategy)
            
            if not result:
                if attempt < max_retries - 1:
                    continue
                else:
                    result = {"thesis": [], "supporting_claims": [], "counterarguments": [], "evidence": []}
            
            quality = self._validate(result)
            
            self.decision_log.append({
                "source_id": source_id,
                "model": self.model_name,
                "article_type": article_type,
                "attempt": attempt + 1,
                "strategy_chosen": strategy,
                "quality_score": quality
            })
            
            if quality >= 0.6 or attempt == max_retries - 1:
                return result
        
        return result

class MultiAgentSystemMultiModel:
    """FIXED: Uses all 7 strategies, not just 4 specialist prompts"""
    
    def __init__(self, model_name):
        self.model_name = model_name
        self.llm_url = "http://localhost:11434/v1/chat/completions"
    
    def _extract_with_strategy(self, text, strategy_name):
        """Extract using one of the 7 strategies"""
        config = STATIC_PROMPTS[strategy_name]
        prompt = config["prompt"].format(text=text[:3500])
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": 1500,
        }
        
        try:
            resp = requests.post(self.llm_url, json=payload, timeout=90)
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
                
                cleaned_items = []
                for item in arg_map[key]:
                    if isinstance(item, dict):
                        cleaned_items.append(' '.join(str(v) for v in item.values() if v))
                    elif isinstance(item, list):
                        cleaned_items.append(' '.join(str(i) for i in item if i))
                    else:
                        cleaned_items.append(str(item))
                
                arg_map[key] = [item.strip() for item in cleaned_items if item and str(item).strip()]
            
            return arg_map
        except:
            return None
    
    def process(self, text, source_id):
        """Run 3 best strategies and aggregate results"""
        strategies_to_try = ["chain_of_thought", "few_shot", "recursive"]
        
        all_results = {
            "thesis": [],
            "supporting_claims": [],
            "counterarguments": [],
            "evidence": []
        }
        
        for strategy in strategies_to_try:
            result = self._extract_with_strategy(text, strategy)
            if result:
                for key in all_results.keys():
                    all_results[key].extend(result.get(key, []))
        
        # Deduplicate
        for key in all_results:
            all_results[key] = list(set(all_results[key]))
        
        return all_results

def main():
    print("\n" + "="*70)
    print("AGENTIC SYSTEMS WITH 3 MODELS (FIXED)")
    print("="*70 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gold_path = os.path.join(script_dir, 'data', 'gold_standard', 'human_annotated_ground_truth_FIXED.json')
    
    with open(gold_path, 'r', encoding='utf-8', errors='ignore') as f:
        gold_standard = json.load(f)
    
    print(f"✓ Loaded {len(gold_standard)} articles\n")
    
    react_results = {model: [] for model in MODELS}
    multiagent_results = {model: [] for model in MODELS}
    all_decisions = []
    
    for idx, article in enumerate(gold_standard):
        source_id = article['source_id']
        url = article.get('url', '')
        title = article.get('title', '')
        
        print(f"\n[{idx+1}/{len(gold_standard)}] {source_id}")
        print(f"   {title[:60]}...")
        
        if not url:
            continue
        
        scraped_title, text = scrape_article(url)
        if not text:
            print(f"   ❌ Scraping failed")
            continue
        
        full_text = f"{title}\n{text}"
        
        for model_name in MODELS:
            print(f"   🤖 {model_name}:")
            
            # ReAct Agent
            print(f"      ReAct...", end="", flush=True)
            react_agent = ReActAgentMultiModel(model_name)
            react_map = react_agent.process(full_text, source_id)
            react_results[model_name].append({
                "source_id": source_id,
                "title": title,
                "url": url,
                "source": article.get('source', ''),
                "topic": article.get('topic', ''),
                "text": full_text,
                "argument_map": react_map
            })
            all_decisions.extend(react_agent.decision_log)
            print(" ✓")
            time.sleep(1)
            
            # Multi-Agent (FIXED)
            print(f"      Multi-Agent...", end="", flush=True)
            multiagent_system = MultiAgentSystemMultiModel(model_name)
            multiagent_map = multiagent_system.process(full_text, source_id)
            multiagent_results[model_name].append({
                "source_id": source_id,
                "title": title,
                "url": url,
                "source": article.get('source', ''),
                "topic": article.get('topic', ''),
                "text": full_text,
                "argument_map": multiagent_map
            })
            print(" ✓")
            time.sleep(1)
    
    # Save
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print("="*70)
    
    output_dir = os.path.join(script_dir, 'data', 'processed', 'agentic_models')
    os.makedirs(output_dir, exist_ok=True)
    
    for model_name in MODELS:
        with open(os.path.join(output_dir, f'{model_name}_react_agent.json'), 'w', encoding='utf-8') as f:
            json.dump(react_results[model_name], f, indent=2, ensure_ascii=False)
        print(f"✓ {model_name} ReAct: {len(react_results[model_name])}")
        
        with open(os.path.join(output_dir, f'{model_name}_multi_agent.json'), 'w', encoding='utf-8') as f:
            json.dump(multiagent_results[model_name], f, indent=2, ensure_ascii=False)
        print(f"✓ {model_name} Multi-Agent: {len(multiagent_results[model_name])}")
    
    with open(os.path.join(output_dir, 'react_agent_decisions.json'), 'w', encoding='utf-8') as f:
        json.dump(all_decisions, f, indent=2)
    
    print(f"\n✅ COMPLETE!\n")

if __name__ == "__main__":
    main()
