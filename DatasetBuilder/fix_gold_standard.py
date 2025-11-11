# save as 

import json
import pandas as pd

print("\n" + "="*70)
print("FIXING GOLD STANDARD - MERGING JSON ANNOTATIONS WITH EXCEL URLs")
print("="*70 + "\n")

# Load both files
with open(r'C:\Users\Mr. Mohit Makde\OneDrive\Desktop\Argument-Cartographer-main\DatasetBuilder\data\gold_standard\human_annotated_ground_truth.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

excel_data = pd.read_excel(r'C:\Users\Mr. Mohit Makde\Downloads\final_articles.xlsx')

print(f"Loaded {len(json_data)} entries from JSON")
print(f"Loaded {len(excel_data)} entries from Excel\n")

# Create Excel lookup by source_id
excel_dict = {}
for _, row in excel_data.iterrows():
    excel_dict[row['source_id']] = {
        'title': row['title'],
        'url': row['url'],
        'topic': row['topic'],
        'source': row['source']
    }

# Merge JSON with Excel data
fixed_data = []
matched = 0
missing = []

for json_entry in json_data:
    source_id = json_entry['source_id']
    
    if source_id in excel_dict:
        # Found matching article in Excel
        excel_info = excel_dict[source_id]
        
        # Create merged entry
        merged = {
            'source_id': source_id,
            'title': excel_info['title'],  # Use Excel title (more accurate)
            'url': excel_info['url'],      # Add URL from Excel
            'topic': excel_info['topic'],
            'source': excel_info['source'],
            'HUMAN_GROUND_TRUTH': json_entry['HUMAN_GROUND_TRUTH']  # Keep annotations
        }
        
        fixed_data.append(merged)
        matched += 1
        print(f"✓ {source_id}: Merged successfully")
    else:
        # No matching article in Excel
        missing.append(source_id)
        print(f"⚠️  {source_id}: Not found in Excel, keeping JSON data only")
        fixed_data.append(json_entry)

# Save fixed version
with open('human_annotated_ground_truth_FIXED.json', 'w', encoding='utf-8') as f:
    json.dump(fixed_data, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print("RESULTS")
print("="*70)
print(f"✓ Successfully merged: {matched}/{len(json_data)}")
print(f"⚠️  Not found in Excel: {len(missing)}")

if missing:
    print(f"\nMissing source IDs: {missing}")

print(f"\n✓ Saved fixed version to: human_annotated_ground_truth_FIXED.json")
print(f"\nNow you can use this FIXED file to run your models!")
print("="*70 + "\n")
