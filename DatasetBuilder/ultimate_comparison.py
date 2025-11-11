from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import json
import numpy as np
import os
import glob

model = SentenceTransformer('all-MiniLM-L6-v2')

def best_similarity(human_list, model_list):
    """Calculate best semantic similarity"""
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

def load_gold_standard(gold_path):
    """Load gold standard with encoding fix"""
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(gold_path, 'r', encoding=encoding, errors='ignore') as f:
                data = json.load(f)
            print(f"✓ Loaded gold standard with {encoding}")
            return data
        except:
            continue
    
    print("ERROR: Could not load gold standard!")
    return None

def evaluate_system(file_path, system_name, gold_standard):
    """Evaluate one system against gold standard"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
    except:
        return None
    
    gold_dict = {e['source_id']: e for e in gold_standard}
    model_dict = {e['source_id']: e for e in data}
    
    scores_dict = {k: [] for k in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']}
    
    for sid in gold_dict.keys():
        if sid not in model_dict:
            continue
        
        gt = gold_dict[sid]['HUMAN_GROUND_TRUTH']
        pred = model_dict[sid].get('argument_map', {})
        
        for key in scores_dict.keys():
            sim = best_similarity(gt.get(key, []), pred.get(key, []))
            scores_dict[key].append(sim)
    
    results = {k: np.mean(v) if v else 0.0 for k, v in scores_dict.items()}
    results['overall'] = np.mean(list(results.values()))
    
    return results

def main():
    print("\n" + "="*90)
    print("ULTIMATE COMPARISON: ALL SYSTEMS")
    print("Static (21) + Agentic (6) = 27 Total Systems")
    print("="*90)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load gold standard with FIX
    gold_path = os.path.join(script_dir, 'data/gold_standard/human_annotated_ground_truth_FIXED.json')
    print(f"\nLoading gold standard...")
    gold_standard = load_gold_standard(gold_path)
    
    if not gold_standard:
        return
    
    print(f"✓ Loaded {len(gold_standard)} gold standard articles\n")
    
    all_scores = {}
    
    # ====================================================================
    # EVALUATE STATIC SYSTEMS
    # ====================================================================
    
    static_dir = os.path.join(script_dir, 'data/processed/static_models')
    static_files = glob.glob(os.path.join(static_dir, '*.json'))
    
    print("Evaluating Static Systems (21)...")
    for filepath in tqdm(static_files, desc="Static"):
        filename = os.path.basename(filepath)
        system_name = filename.replace('.json', '').replace('_', ' ').title()
        scores = evaluate_system(filepath, system_name, gold_standard)
        if scores:
            all_scores[f"Static: {system_name}"] = scores
    
    # ====================================================================
    # EVALUATE AGENTIC SYSTEMS
    # ====================================================================
    
    agentic_dir = os.path.join(script_dir, 'data/processed/agentic_models')
    agentic_files = glob.glob(os.path.join(agentic_dir, '*.json'))
    agentic_files = [f for f in agentic_files if 'decisions' not in f]
    
    print("\nEvaluating Agentic Systems (6)...")
    for filepath in tqdm(agentic_files, desc="Agentic"):
        filename = os.path.basename(filepath)
        system_name = filename.replace('.json', '').replace('_', ' ').title()
        scores = evaluate_system(filepath, system_name, gold_standard)
        if scores:
            all_scores[f"Agentic: {system_name}"] = scores
    
    # ====================================================================
    # SORT AND DISPLAY
    # ====================================================================
    
    sorted_systems = sorted(all_scores.items(), key=lambda x: x[1]['overall'], reverse=True)
    
    print("\n" + "="*90)
    print("TOP 10 PERFORMING SYSTEMS")
    print("="*90)
    print(f"{'Rank':<5} {'System':<50} {'Overall':<12} {'Best Category'}")
    print("-"*90)
    
    for rank, (name, scores) in enumerate(sorted_systems[:10], 1):
        best_cat = max(scores.items(), key=lambda x: x[1] if x[0] != 'overall' else 0)
        print(f"{rank:<5} {name:<50} {scores['overall']:.4f}     {best_cat[0]}: {best_cat[1]:.4f}")
    
    # ====================================================================
    # CATEGORY WINNERS
    # ====================================================================
    
    print("\n" + "="*90)
    print("BEST PERFORMERS BY CATEGORY")
    print("="*90)
    
    for category in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
        best_system, best_scores = max(all_scores.items(), key=lambda x: x[1][category])
        print(f"{category.replace('_', ' ').title():<25}: {best_system:<50} {best_scores[category]:.4f}")
    
    # ====================================================================
    # STATIC vs AGENTIC
    # ====================================================================
    
    print("\n" + "="*90)
    print("STATIC vs AGENTIC COMPARISON")
    print("="*90)
    
    static_scores = [s for name, s in all_scores.items() if 'Static:' in name]
    agentic_scores = [s for name, s in all_scores.items() if 'Agentic:' in name]
    
    if static_scores and agentic_scores:
        static_avg = np.mean([s['overall'] for s in static_scores])
        agentic_avg = np.mean([s['overall'] for s in agentic_scores])
        improvement = ((agentic_avg - static_avg) / static_avg * 100)
        
        print(f"Average Static Performance:  {static_avg:.4f} ({static_avg*100:.2f}%)")
        print(f"Average Agentic Performance: {agentic_avg:.4f} ({agentic_avg*100:.2f}%)")
        print(f"\nImprovement: {improvement:+.2f}%")
        
        if improvement > 0:
            print(f"✅ AGENTIC AI OUTPERFORMS STATIC BY {improvement:.2f}%!")
    
    # ====================================================================
    # MODEL COMPARISON
    # ====================================================================
    
    print("\n" + "="*90)
    print("MODEL COMPARISON")
    print("="*90)
    
    for model in ["llama3.1", "llama3.2", "gemma2"]:
        model_scores = [s['overall'] for name, s in all_scores.items() if model in name.lower()]
        if model_scores:
            avg = np.mean(model_scores)
            print(f"{model:<15}: {avg:.4f} ({avg*100:.2f}%) - {len(model_scores)} configurations")
    
    # ====================================================================
    # AGENT TYPE COMPARISON
    # ====================================================================
    
    print("\n" + "="*90)
    print("AGENT TYPE COMPARISON")
    print("="*90)
    
    react_scores = [s['overall'] for name, s in all_scores.items() if 'react' in name.lower()]
    multiagent_scores = [s['overall'] for name, s in all_scores.items() if 'multi' in name.lower()]
    
    if react_scores:
        react_avg = np.mean(react_scores)
        print(f"ReAct Agent:     {react_avg:.4f} ({react_avg*100:.2f}%)")
    
    if multiagent_scores:
        multiagent_avg = np.mean(multiagent_scores)
        print(f"Multi-Agent:     {multiagent_avg:.4f} ({multiagent_avg*100:.2f}%)")
    
    # ====================================================================
    # DETAILED TABLE
    # ====================================================================
    
    print("\n" + "="*90)
    print("DETAILED SYSTEM-BY-SYSTEM BREAKDOWN")
    print("="*90)
    print(f"{'System':<50} {'Thesis':<12} {'Claims':<12} {'Counter':<12} {'Evidence':<12} {'Overall':<12}")
    print("-"*90)
    
    for name, scores in sorted_systems:
        print(f"{name:<50} {scores['thesis']:.4f}     {scores['supporting_claims']:.4f}     "
              f"{scores['counterarguments']:.4f}     {scores['evidence']:.4f}     {scores['overall']:.4f}")
    
    # ====================================================================
    # SAVE RESULTS
    # ====================================================================
    
    output_file = os.path.join(script_dir, 'data/processed/ultimate_comparison.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_scores, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*90)
    print("✅ COMPARISON COMPLETE!")
    print("="*90)
    print(f"Results saved to: ultimate_comparison.json\n")

if __name__ == "__main__":
    main()
