from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import json
import numpy as np
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

def best_similarity(human_list, model_list):
    if not human_list or not model_list:
        return 0.0
    scores = []
    for h in human_list:
        h_emb = model.encode(h, convert_to_tensor=True)
        best = 0.0
        for m in model_list:
            m_emb = model.encode(m, convert_to_tensor=True)
            sim = util.pytorch_cos_sim(h_emb, m_emb).item()
            if sim > best:
                best = sim
        scores.append(best)
    return np.mean(scores) if scores else 0.0

def evaluate_model(model_file, model_name, gold_standard):
    print(f"\nLoading {model_name}...")
    with open(model_file, 'r', encoding='utf-8') as f:
        model_data = json.load(f)
    
    gold_dict = {entry['source_id']: entry for entry in gold_standard}
    model_dict = {entry['source_id']: entry for entry in model_data}
    
    all_scores = {k: [] for k in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']}
    
    for source_id in tqdm(gold_dict.keys(), desc=f"Evaluating {model_name}"):
        if source_id not in model_dict:
            continue
        
        ground_truth = gold_dict[source_id]['HUMAN_GROUND_TRUTH']
        model_extraction = model_dict[source_id].get('argument_map', {})
        
        for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
            human_args = ground_truth.get(key, [])
            model_args = model_extraction.get(key, [])
            sim_score = best_similarity(human_args, model_args)
            all_scores[key].append(sim_score)
    
    results = {}
    for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
        results[key] = np.mean(all_scores[key]) if all_scores[key] else 0.0
    results['overall'] = np.mean(list(results.values()))
    
    return results

def main():
    print("\n" + "="*80)
    print("FRESH MODEL COMPARISON: BASELINE vs ENHANCED vs IMPROVED")
    print("All models processed on same gold standard articles")
    print("="*80)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    gold_path = os.path.join(script_dir, 'data', 'gold_standard', 'human_annotated_ground_truth_FIXED.json')
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    print(f"\n✓ Loaded {len(gold_standard)} gold standard articles")
    
    baseline_scores = evaluate_model(
        os.path.join(script_dir, 'data', 'processed', 'baseline_model_fresh.json'),
        'Baseline', gold_standard
    )
    enhanced_scores = evaluate_model(
        os.path.join(script_dir, 'data', 'processed', 'enhanced_model_fresh.json'),
        'Enhanced', gold_standard
    )
    improved_scores = evaluate_model(
        os.path.join(script_dir, 'data', 'processed', 'improved_model_fresh.json'),
        'Improved', gold_standard
    )
    
    print("\n" + "="*80)
    print("SEMANTIC SIMILARITY RESULTS")
    print("="*80)
    print(f"{'Category':<20} {'Baseline':<15} {'Enhanced':<15} {'Improved':<15}")
    print("-"*80)
    
    for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence', 'overall']:
        baseline = baseline_scores[key]
        enhanced = enhanced_scores[key]
        improved = improved_scores[key]
        
        print(f"{key.replace('_', ' ').title():<20} "
              f"{baseline:.3f} ({baseline*100:.1f}%)  "
              f"{enhanced:.3f} ({enhanced*100:.1f}%)  "
              f"{improved:.3f} ({improved*100:.1f}%)")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
