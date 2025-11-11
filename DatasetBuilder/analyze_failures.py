# save as verify_article_match.py

import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# Load all datasets
print("\n" + "="*70)
print("VERIFYING ARTICLE MATCHING")
print("="*70 + "\n")

# Load gold standard
gold_path = os.path.join(script_dir, 'data', 'gold_standard', 'human_annotated_ground_truth.json')
with open(gold_path, 'r', encoding='utf-8') as f:
    gold_standard = json.load(f)

# Load baseline
baseline_path = os.path.join(script_dir, 'data', 'processed', 'reputable_news_dataset_cleaned.json')
with open(baseline_path, 'r', encoding='utf-8') as f:
    baseline = json.load(f)

# Load improved
try:
    improved_path = os.path.join(script_dir, 'data', 'processed', 'improved_model_dataset_v2.json')
    with open(improved_path, 'r', encoding='utf-8') as f:
        improved = json.load(f)
except:
    improved = []

# Extract source IDs
gold_ids = set([a['source_id'] for a in gold_standard])
baseline_ids = set([a['source_id'] for a in baseline])
improved_ids = set([a['source_id'] for a in improved]) if improved else set()

print(f"Gold Standard:    {len(gold_ids)} articles")
print(f"Baseline Model:   {len(baseline_ids)} articles")
print(f"Improved Model:   {len(improved_ids)} articles")

print(f"\n{'='*70}")
print("ARTICLE ID COMPARISON")
print("="*70)

# Check overlap
gold_in_baseline = gold_ids & baseline_ids
gold_in_improved = gold_ids & improved_ids

print(f"\nGold standard articles found in Baseline: {len(gold_in_baseline)}/{len(gold_ids)}")
print(f"Gold standard articles found in Improved: {len(gold_in_improved)}/{len(gold_ids)}")

# Show missing articles
missing_from_baseline = gold_ids - baseline_ids
missing_from_improved = gold_ids - improved_ids

if missing_from_baseline:
    print(f"\n⚠️  MISSING FROM BASELINE: {len(missing_from_baseline)} articles")
    print(f"Missing IDs: {sorted(missing_from_baseline)}")
else:
    print(f"\n✅ All gold standard articles are in baseline!")

if improved:
    if missing_from_improved:
        print(f"\n⚠️  MISSING FROM IMPROVED: {len(missing_from_improved)} articles")
        print(f"Missing IDs: {sorted(missing_from_improved)}")
    else:
        print(f"\n✅ All gold standard articles are in improved model!")

# Show sample URLs to verify
print(f"\n{'='*70}")
print("SAMPLE URL VERIFICATION (First 3 gold standard articles)")
print("="*70)

gold_dict = {a['source_id']: a for a in gold_standard}
baseline_dict = {a['source_id']: a for a in baseline}
improved_dict = {a['source_id']: a for a in improved} if improved else {}

for i, source_id in enumerate(sorted(gold_ids)[:3], 1):
    print(f"\n{i}. {source_id}")
    
    gold_article = gold_dict.get(source_id, {})
    baseline_article = baseline_dict.get(source_id, {})
    
    print(f"   Gold Standard Title: {gold_article.get('title', 'N/A')[:60]}...")
    
    if source_id in baseline_dict:
        print(f"   Baseline Title:      {baseline_article.get('title', 'N/A')[:60]}...")
        print(f"   Baseline URL:        {baseline_article.get('url', 'N/A')}")
        
        # Check if URLs match
        if gold_article.get('url') and baseline_article.get('url'):
            if gold_article['url'] == baseline_article['url']:
                print(f"   ✅ URLs MATCH")
            else:
                print(f"   ⚠️  URLs DIFFER!")
                print(f"   Gold URL: {gold_article['url']}")
    else:
        print(f"   ❌ NOT IN BASELINE")

print("\n" + "="*70 + "\n")
