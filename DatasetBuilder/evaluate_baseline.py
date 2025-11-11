# save as evaluate_baseline.py
# Run from: C:\Users\Mr. Mohit Makde\OneDrive\Desktop\Argument-Cartographer-main

import json


def calculate_f1_score(predicted, ground_truth):
    """Calculate F1 score based on element counts"""
    
    scores = {}
    
    for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
        pred_count = len(predicted.get(key, []))
        true_count = len(ground_truth.get(key, []))
        
        # Perfect match
        if pred_count == true_count:
            score = 1.0
        # Over or under extraction
        elif true_count == 0:
            score = 0.0 if pred_count > 0 else 1.0
        else:
            # Penalize over/under extraction
            score = 1.0 - abs(pred_count - true_count) / max(pred_count, true_count)
        
        scores[key] = score
    
    # Overall accuracy
    overall = sum(scores.values()) / len(scores)
    
    return overall, scores


def evaluate_baseline():
    # Load gold standard - WITH DatasetBuilder prefix
    with open('DatasetBuilder/data/gold_standard/human_annotated_ground_truth.json', 'r', encoding='utf-8') as f:
        gold_standard = json.load(f)
    
    # Load baseline dataset - WITH DatasetBuilder prefix
    with open('DatasetBuilder/data/processed/reputable_news_dataset_cleaned.json', 'r', encoding='utf-8') as f:
        baseline_data = json.load(f)
    
    # Match by source_id
    baseline_dict = {entry['source_id']: entry for entry in baseline_data}
    
    results = []
    all_scores = []
    
    print(f"\n{'='*70}")
    print("BASELINE MODEL EVALUATION AGAINST HUMAN GROUND TRUTH")
    print(f"{'='*70}\n")
    
    for gold_entry in gold_standard:
        source_id = gold_entry.get('source_id', 'unknown')
        
        if source_id not in baseline_dict:
            print(f"⚠ Skipping {source_id} - not in baseline dataset")
            continue
        
        baseline_extraction = baseline_dict[source_id].get('argument_map', {})
        ground_truth = gold_entry.get('HUMAN_GROUND_TRUTH', {})
        
        # Skip if missing data
        if not baseline_extraction or not ground_truth:
            print(f"⚠ Skipping {source_id} - missing extraction or ground truth")
            continue
        
        overall, detailed = calculate_f1_score(baseline_extraction, ground_truth)
        all_scores.append(overall)
        
        # Get title safely
        title = gold_entry.get('title', baseline_dict[source_id].get('title', 'Unknown'))
        
        results.append({
            "source_id": source_id,
            "title": title[:50] + "..." if len(title) > 50 else title,
            "overall_accuracy": overall,
            "thesis_score": detailed['thesis'],
            "claims_score": detailed['supporting_claims'],
            "counter_score": detailed['counterarguments'],
            "evidence_score": detailed['evidence']
        })
        
        # Show individual article scores
        print(f"{source_id}: {overall*100:.1f}% | T:{detailed['thesis']*100:.0f}% C:{detailed['supporting_claims']*100:.0f}% CT:{detailed['counterarguments']*100:.0f}% E:{detailed['evidence']*100:.0f}%")
    
    if not all_scores:
        print("\n❌ No matching articles found!")
        print("   Check that source_id values match between:")
        print("   - DatasetBuilder/data/gold_standard/human_annotated_ground_truth.json")
        print("   - DatasetBuilder/data/processed/reputable_news_dataset_cleaned.json")
        return
    
    # Calculate averages
    avg_overall = sum(all_scores) / len(all_scores) * 100
    
    print(f"\n{'='*70}")
    print(f"BASELINE MODEL RESULTS")
    print(f"{'='*70}")
    print(f"Evaluated on: {len(results)} articles")
    print(f"Average Accuracy: {avg_overall:.1f}%")
    
    # Category breakdown
    avg_thesis = sum(r['thesis_score'] for r in results) / len(results) * 100
    avg_claims = sum(r['claims_score'] for r in results) / len(results) * 100
    avg_counter = sum(r['counter_score'] for r in results) / len(results) * 100
    avg_evidence = sum(r['evidence_score'] for r in results) / len(results) * 100
    
    print(f"\nCategory Breakdown:")
    print(f"  Thesis Accuracy: {avg_thesis:.1f}%")
    print(f"  Supporting Claims: {avg_claims:.1f}%")
    print(f"  Counterarguments: {avg_counter:.1f}%")
    print(f"  Evidence: {avg_evidence:.1f}%")
    print(f"{'='*70}\n")
    
    # Save results - WITH DatasetBuilder prefix
    with open('DatasetBuilder/data/processed/baseline_evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "average_accuracy": avg_overall,
            "category_scores": {
                "thesis": avg_thesis,
                "supporting_claims": avg_claims,
                "counterarguments": avg_counter,
                "evidence": avg_evidence
            },
            "individual_results": results
        }, f, indent=2, ensure_ascii=False)
    
    print("✓ Results saved to DatasetBuilder/data/processed/baseline_evaluation_results.json")


if __name__ == "__main__":
    evaluate_baseline()
