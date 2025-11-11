no need to run this 

# from ddgs import DDGS
# import requests
# from bs4 import BeautifulSoup
# import time
# import json
# from datetime import datetime

# def scrape_news_sites():
#     print("🚀 Starting news scraping process...")
    
#     try:
#         ddgs = DDGS()
#         print("✅ DDGS initialized successfully")
        
#         # Get news results first
#         print("🔍 Searching for news articles...")
#         results = ddgs.news(query="madhuri elephant kolhapur", max_results=5)
        
#         if not results:
#             print("❌ No news results found!")
#             return
            
#         print(f"✅ Found {len(results)} news articles")
        
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
#         }
        
#         scraped_articles = []
        
#         for i, result in enumerate(results, 1):
#             url = result['url']
#             title = result['title']
            
#             print(f"\n📰 [{i}/{len(results)}] Scraping: {title[:50]}...")
#             print(f"🔗 URL: {url}")
            
#             try:
#                 print("   ⏳ Downloading page content...")
#                 response = requests.get(url, headers=headers, timeout=10)
#                 response.raise_for_status()
                
#                 print("   🔧 Parsing HTML...")
#                 soup = BeautifulSoup(response.content, 'html.parser')
                
#                 # Extract article content
#                 print("   📝 Extracting article content...")
#                 article_text = extract_article_content(soup)
                
#                 # Store the scraped data
#                 article_data = {
#                     'title': title,
#                     'url': url,
#                     'content': article_text,
#                     'scraped_at': datetime.now().isoformat()
#                 }
#                 scraped_articles.append(article_data)
                
#                 print(f"   ✅ Successfully scraped! Content length: {len(article_text)} characters")
#                 print(f"   📄 Preview: {article_text[:100]}...")
                
#                 time.sleep(2)  # Be respectful with delays
                
#             except Exception as e:
#                 print(f"   ❌ Failed to scrape: {e}")
#                 # Still add to results with error info
#                 article_data = {
#                     'title': title,
#                     'url': url,
#                     'content': f"ERROR: {str(e)}",
#                     'scraped_at': datetime.now().isoformat()
#                 }
#                 scraped_articles.append(article_data)
        
#         # Save results to files
#         print(f"\n💾 Saving results to files...")
#         save_results(scraped_articles)
#         print("🎉 Scraping completed successfully!")
        
#     except Exception as e:
#         print(f"❌ Critical error during scraping: {e}")

# def extract_article_content(soup):
#     # Try common article selectors
#     selectors = [
#         'article p',
#         '.article-content p',
#         '.post-content p',
#         '.entry-content p',
#         'div[class*="content"] p',
#         '.story-body p',
#         '.article-body p',
#         'main p',
#         'p'
#     ]
    
#     for selector in selectors:
#         paragraphs = soup.select(selector)
#         if paragraphs and len(paragraphs) > 2:  # Ensure we have substantial content
#             content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
#             if len(content) > 100:  # Only return if we have meaningful content
#                 return content
    
#     return "Content not found or insufficient content"

# def save_results(articles):
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
#     # Save as JSON file
#     json_filename = f"scraped_news_{timestamp}.json"
#     with open(json_filename, 'w', encoding='utf-8') as f:
#         json.dump(articles, f, indent=2, ensure_ascii=False)
#     print(f"✅ JSON file saved: {json_filename}")
    
#     # Save as readable text file
#     txt_filename = f"scraped_news_{timestamp}.txt"
#     with open(txt_filename, 'w', encoding='utf-8') as f:
#         f.write(f"News Scraping Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
#         f.write("=" * 80 + "\n\n")
        
#         for i, article in enumerate(articles, 1):
#             f.write(f"ARTICLE {i}\n")
#             f.write("-" * 40 + "\n")
#             f.write(f"Title: {article['title']}\n")
#             f.write(f"URL: {article['url']}\n")
#             f.write(f"Scraped At: {article['scraped_at']}\n")
#             f.write(f"Content:\n{article['content']}\n")
#             f.write("\n" + "=" * 80 + "\n\n")
    
#     print(f"✅ Text file saved: {txt_filename}")

# if __name__ == "__main__":
#     scrape_news_sites()
