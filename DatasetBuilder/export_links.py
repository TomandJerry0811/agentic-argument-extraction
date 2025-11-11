import json
import csv

def export_links_titles_topics_sources():
    # Load your cleaned dataset
    with open('data/processed/reputable_news_dataset_cleaned.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Output CSV file path
    output_csv = 'data/processed/article_links_for_review.csv'
    
    # Write to CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['source_id', 'title', 'topic', 'source', 'url'])  # header
        
        for entry in dataset:
            writer.writerow([
                entry.get('source_id', ''),
                entry.get('title', ''),
                entry.get('topic', ''),
                entry.get('source', ''),
                entry.get('url', '')
            ])
    
    print(f"\n✓ Exported {len(dataset)} articles to {output_csv}")
    print("Open this file in Excel or Google Sheets for manual review.")

if __name__ == "__main__":
    export_links_titles_topics_sources()
