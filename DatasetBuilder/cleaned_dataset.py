import json

def validate_and_clean_dataset():
    """Filter out off-topic and low-quality extractions"""
    
    # Load the dataset created by dataset_builder.py
    with open('data/processed/reputable_news_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    cleaned = []
    removed = []
    
    for entry in dataset:
        arg_map = entry['argument_map']
        
        # Check 1: Minimum content threshold
        total_elements = sum(len(arg_map.get(k, [])) for k in arg_map if isinstance(arg_map.get(k), list))
        if total_elements < 3:  # At least 3 total elements
            removed.append({
                "reason": "Too few elements",
                "source_id": entry['source_id'],
                "title": entry['title']
            })
            continue
        
        # Check 2: Must have thesis
        if not arg_map.get('thesis') or len(arg_map['thesis']) == 0:
            removed.append({
                "reason": "No thesis",
                "source_id": entry['source_id'],
                "title": entry['title']
            })
            continue
        
        # Check 3: Fix evidence format if needed
        if arg_map.get('evidence'):
            evidence = arg_map['evidence']
            # Convert objects to strings if needed
            if isinstance(evidence, list) and len(evidence) > 0:
                if isinstance(evidence[0], dict):
                    arg_map['evidence'] = [
                        f"{e.get('quote', '')} - {e.get('source', '')}" 
                        for e in evidence if isinstance(e, dict)
                    ]
        
        cleaned.append(entry)
    
    # Save cleaned dataset
    with open('data/processed/reputable_news_dataset_cleaned.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    
    # Save removal report
    with open('data/processed/removed_entries.json', 'w', encoding='utf-8') as f:
        json.dump(removed, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("DATASET CLEANING COMPLETE")
    print(f"{'='*60}")
    print(f"Original entries: {len(dataset)}")
    print(f"Cleaned entries: {len(cleaned)}")
    print(f"Removed entries: {len(removed)}")
    print(f"\n✓ Cleaned dataset saved to:")
    print(f"  data/processed/reputable_news_dataset_cleaned.json")
    
    if removed:
        print(f"\nRemoved entries (saved to removed_entries.json):")
        for r in removed[:10]:  # Show first 10
            print(f"  - {r['title'][:60]}... ({r['reason']})")
        if len(removed) > 10:
            print(f"  ... and {len(removed) - 10} more")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    validate_and_clean_dataset()
