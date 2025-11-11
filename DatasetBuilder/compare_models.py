from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import json
import numpy as np
import os

# Load SBERT model for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

def best_similarity(human_list, model_list):
    """Calculate best semantic similarity between human and model extractions"""
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
    """Evaluate a model against gold standard"""
    
    # Load model output
    print(f"\nLoading {model_name} data...")
    with open(model_file, 'r', encoding='utf-8') as f:
        model_data = json.load(f)
    
    gold_dict = {entry['source_id']: entry for entry in gold_standard}
    model_dict = {entry['source_id']: entry for entry in model_data}
    
    all_scores = {k: [] for k in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']}
    
    print(f"Evaluating {model_name} against gold standard...")
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
    
    # Calculate averages
    results = {}
    for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
        results[key] = np.mean(all_scores[key]) if all_scores[key] else 0.0
    results['overall'] = np.mean(list(results.values()))
    
    return results

def main():
    print("\n" + "="*70)
    print("MODEL COMPARISON: BASELINE vs ENHANCED")
    print("="*70)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build paths relative to script location
    gold_standard_path = os.path.join(script_dir, 'data', 'gold_standard', 'human_annotated_ground_truth.json')
    baseline_path = os.path.join(script_dir, 'data', 'processed', 'reputable_news_dataset_cleaned.json')
    enhanced_path = os.path.join(script_dir, 'data', 'processed', 'enhanced_model_dataset.json')
    output_path = os.path.join(script_dir, 'data', 'processed', 'model_comparison_results.json')
    
    # Load gold standard
    print("\nLoading gold standard (human annotations)...")
    print(f"Path: {gold_standard_path}")
    with open(gold_standard_path, 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    print(f"✓ Loaded {len(gold_standard)} human-annotated articles")
    
    # Evaluate both models
    baseline_scores = evaluate_model(baseline_path, 'Baseline Model', gold_standard)
    enhanced_scores = evaluate_model(enhanced_path, 'Enhanced Model', gold_standard)
    
    # Print comparison table
    print("\n" + "="*70)
    print("SEMANTIC SIMILARITY RESULTS")
    print("="*70)
    print(f"{'Category':<20} {'Baseline':<18} {'Enhanced':<18} {'Improvement'}")
    print("-"*70)
    
    for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence', 'overall']:
        baseline = baseline_scores[key]
        enhanced = enhanced_scores[key]
        improvement = ((enhanced - baseline) / baseline * 100) if baseline > 0 else 0
        
        # Color code improvement
        symbol = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
        
        print(f"{key.replace('_', ' ').title():<20} "
              f"{baseline:.3f} ({baseline*100:.1f}%)    "
              f"{enhanced:.3f} ({enhanced*100:.1f}%)    "
              f"{symbol} {improvement:+.1f}%")
    
    print("="*70 + "\n")
    
    # Save detailed comparison
    comparison_results = {
        'baseline': {
            'scores': baseline_scores,
            'file': baseline_path
        },
        'enhanced': {
            'scores': enhanced_scores,
            'file': enhanced_path
        },
        'improvement': {
            key: ((enhanced_scores[key] - baseline_scores[key]) / baseline_scores[key] * 100) 
            if baseline_scores[key] > 0 else 0
            for key in baseline_scores.keys()
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    print(f"✓ Detailed comparison saved to: {output_path}\n")

if __name__ == "__main__":
    main()
