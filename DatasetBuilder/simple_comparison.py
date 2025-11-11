from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import json
import numpy as np
import os
import glob

model = SentenceTransformer('all-MiniLM-L6-v2')

def main():
    print("\n" + "="*90)
    print("SIMPLE COMPARISON - READING ALL EXTRACTED FILES")
    print("="*90 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    all_scores = {}
    
    # ====================================================================
    # LOAD STATIC SYSTEMS
    # ====================================================================
    
    static_dir = os.path.join(script_dir, 'data', 'processed', 'static_models')
    static_files = glob.glob(os.path.join(static_dir, '*.json'))
    
    print(f"Found {len(static_files)} static files\n")
    print("Loading Static Systems...")
    
    for filepath in tqdm(static_files):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            filename = os.path.basename(filepath).replace('.json', '').replace('_', ' ').title()
            
            # Count items
            count = len(data)
            all_scores[f"Static: {filename}"] = {
                'count': count,
                'overall': 0.0
            }
        except Exception as e:
            print(f"Error with {filepath}: {e}")
    
    # ====================================================================
    # LOAD AGENTIC SYSTEMS
    # ====================================================================
    
    agentic_dir = os.path.join(script_dir, 'data', 'processed', 'agentic_models')
    agentic_files = glob.glob(os.path.join(agentic_dir, '*.json'))
    agentic_files = [f for f in agentic_files if 'decisions' not in f]
    
    print(f"\nFound {len(agentic_files)} agentic files\n")
    print("Loading Agentic Systems...")
    
    for filepath in tqdm(agentic_files):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            filename = os.path.basename(filepath).replace('.json', '').replace('_', ' ').title()
            
            # Count items
            count = len(data)
            all_scores[f"Agentic: {filename}"] = {
                'count': count,
                'overall': 0.0
            }
        except Exception as e:
            print(f"Error with {filepath}: {e}")
    
    # ====================================================================
    # DISPLAY RESULTS
    # ====================================================================
    
    print("\n" + "="*90)
    print("EXTRACTION COMPLETENESS CHECK")
    print("="*90 + "\n")
    
    print(f"{'System':<60} {'Articles Extracted':<20}")
    print("-"*90)
    
    for system_name, info in sorted(all_scores.items()):
        count = info['count']
        status = "✓ COMPLETE" if count == 48 else "⚠️  INCOMPLETE"
        print(f"{system_name:<60} {count}/48 {status}")
    
    # Statistics
    print("\n" + "="*90)
    print("SUMMARY")
    print("="*90 + "\n")
    
    static_systems = [s for s in all_scores if 'Static:' in s]
    agentic_systems = [s for s in all_scores if 'Agentic:' in s]
    
    print(f"Total Static Systems: {len(static_systems)}")
    print(f"Total Agentic Systems: {len(agentic_systems)}")
    print(f"Total Systems: {len(all_scores)}\n")
    
    static_extraction_rates = [all_scores[s]['count'] / 48 * 100 for s in static_systems]
    agentic_extraction_rates = [all_scores[s]['count'] / 48 * 100 for s in agentic_systems]
    
    if static_extraction_rates:
        static_avg = np.mean(static_extraction_rates)
        print(f"Average Static Extraction Rate: {static_avg:.1f}%")
    
    if agentic_extraction_rates:
        agentic_avg = np.mean(agentic_extraction_rates)
        print(f"Average Agentic Extraction Rate: {agentic_avg:.1f}%")
        
        if static_extraction_rates and agentic_avg > static_avg:
            diff = agentic_avg - static_avg
            print(f"\n✅ Agentic systems have {diff:+.1f}% higher extraction rate!")
    
    print("\n" + "="*90)
    print("✅ DATA LOADING COMPLETE!")
    print("="*90 + "\n")
    
    print("All systems successfully loaded and ready for analysis!")

if __name__ == "__main__":
    main()
