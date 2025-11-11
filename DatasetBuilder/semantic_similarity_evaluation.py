from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import json
import numpy as np

# Load SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load gold standard and your model output
with open('DatasetBuilder/data/gold_standard/human_annotated_ground_truth.json', 'r', encoding='utf-8') as f:
    gold_standard = json.load(f)

with open('DatasetBuilder/data/processed/reputable_news_dataset_cleaned.json', 'r', encoding='utf-8') as f:
    your_model_data = json.load(f)

# Create dict for quick lookup by source_id
gold_dict = {entry['source_id']: entry for entry in gold_standard}
model_dict = {entry['source_id']: entry for entry in your_model_data}

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

results = []
all_scores = {k: [] for k in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']}

print("\nComparing Your Model Output to Gold Standard (Semantic Similarity)\n" + "="*70)
for source_id in tqdm(gold_dict.keys(), desc="Evaluating articles"):
    if source_id not in model_dict:
        print(f"⚠ Skipping {source_id} - not in your model output")
        continue

    gold_entry = gold_dict[source_id]
    model_entry = model_dict[source_id]

    ground_truth = gold_entry['HUMAN_GROUND_TRUTH']
    model_extraction = model_entry.get('argument_map', {})

    scores = {}
    for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
        human_args = ground_truth.get(key, [])
        model_args = model_extraction.get(key, [])
        sim_score = best_similarity(human_args, model_args)
        scores[key] = sim_score
        all_scores[key].append(sim_score)

    overall = np.mean(list(scores.values()))
    results.append({
        "source_id": source_id,
        "title": gold_entry.get('title', '')[:50],
        "overall_similarity": overall,
        "thesis_similarity": scores['thesis'],
        "claims_similarity": scores['supporting_claims'],
        "counter_similarity": scores['counterarguments'],
        "evidence_similarity": scores['evidence']
    })

# Calculate averages
print("\n" + "="*70)
print("AVERAGE SEMANTIC SIMILARITY SCORES")
print("="*70)
for key in ['thesis', 'supporting_claims', 'counterarguments', 'evidence']:
    avg = np.mean(all_scores[key])
    print(f"{key.capitalize():18}: {avg:.2f}")
overall_avg = np.mean([r["overall_similarity"] for r in results])
print(f"\nOverall Average Similarity: {overall_avg:.2f}")

# Save results
with open('DatasetBuilder/data/processed/your_model_semantic_similarity_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\n✓ Results saved to DatasetBuilder/data/processed/your_model_semantic_similarity_results.json")
