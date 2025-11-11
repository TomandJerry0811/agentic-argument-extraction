# save as convert_gold_standard.py

from docx import Document
import json

def parse_gold_standard_from_word(docx_path):
    """Automatically parse all articles from Word document"""
    
    doc = Document(r"C:\Users\Mr. Mohit Makde\OneDrive\Desktop\Argument-Cartographer-main\DatasetBuilder\FinalMergedRules.docx")
    
    # Get all text lines
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    
    # Parse articles
    gold_standard = []
    i = 0
    
    while i < len(full_text):
        line = full_text[i]
        
        # Check if this is the start of a new article
        if line.startswith("ID:") or line.startswith("ID :"):
            article = {}
            
            # Extract ID
            source_id = line.split(":", 1)[1].strip()
            article['source_id'] = source_id
            i += 1
            
            # Extract ARTICLE title
            if i < len(full_text) and full_text[i].startswith("ARTICLE:"):
                article['title'] = full_text[i].split(":", 1)[1].strip()
                i += 1
            
            # Extract TOPIC
            if i < len(full_text) and full_text[i].startswith("TOPIC:"):
                article['topic'] = full_text[i].split(":", 1)[1].strip()
                i += 1
            
            # Initialize ground truth
            ground_truth = {
                "thesis": [],
                "supporting_claims": [],
                "counterarguments": [],
                "evidence": []
            }
            
            current_section = None
            
            # Parse sections until next article
            while i < len(full_text):
                line = full_text[i]
                
                # Check if we hit next article
                if line.startswith("ID:") or line.startswith("ID :"):
                    break
                
                # Check section headers
                if line == "THESIS:":
                    current_section = "thesis"
                    i += 1
                    continue
                elif line == "SUPPORTING CLAIMS:":
                    current_section = "supporting_claims"
                    i += 1
                    continue
                elif line == "COUNTERARGUMENTS:":
                    current_section = "counterarguments"
                    i += 1
                    continue
                elif line == "EVIDENCE:":
                    current_section = "evidence"
                    i += 1
                    continue
                
                # Add content to current section
                if current_section and line:
                    # Remove bullet points and quotes
                    clean_line = line.strip().strip('"').strip('"').strip('"').strip('•').strip('-').strip()
                    if clean_line:
                        ground_truth[current_section].append(clean_line)
                
                i += 1
            
            article['HUMAN_GROUND_TRUTH'] = ground_truth
            gold_standard.append(article)
        else:
            i += 1
    
    return gold_standard

def main():
    # Parse Word document
    gold_standard = parse_gold_standard_from_word('FinalMergedRules.docx')
    
    # Save to JSON
    with open('DatasetBuilder/data/gold_standard/human_annotated_ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(gold_standard, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Automatically parsed {len(gold_standard)} articles from Word document")
    print(f"✓ Saved to data/gold_standard/human_annotated_ground_truth.json")
    
    # Show summary
    print(f"\nSummary:")
    print(f"  Total articles: {len(gold_standard)}")
    print(f"  Average thesis per article: {sum(len(a['HUMAN_GROUND_TRUTH']['thesis']) for a in gold_standard) / len(gold_standard):.1f}")
    print(f"  Average claims per article: {sum(len(a['HUMAN_GROUND_TRUTH']['supporting_claims']) for a in gold_standard) / len(gold_standard):.1f}")
    print(f"  Average counterargs per article: {sum(len(a['HUMAN_GROUND_TRUTH']['counterarguments']) for a in gold_standard) / len(gold_standard):.1f}")
    print(f"  Average evidence per article: {sum(len(a['HUMAN_GROUND_TRUTH']['evidence']) for a in gold_standard) / len(gold_standard):.1f}")

if __name__ == "__main__":
    main()
