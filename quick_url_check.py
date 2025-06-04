"""
Quick script to check a sample of URLs to assess the overall data quality.
"""

import requests
import re
import concurrent.futures
import time
from typing import List, Tuple

def load_sample_urls(file_path: str, sample_size: int = 50) -> List[str]:
    """Load a sample of URLs from the file."""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            content = file.read().strip()
            
        url_pattern = r'\[([^]]+)\]'
        urls = re.findall(url_pattern, content)
        
        valid_urls = [
            url.strip() for url in urls 
            if url.strip() and 'cdn.discordapp.com' in url
        ]
        
        # Take sample from different parts of the file
        step = len(valid_urls) // sample_size if len(valid_urls) > sample_size else 1
        sample = valid_urls[::step][:sample_size]
        
        print(f"Checking sample of {len(sample)} URLs from {len(valid_urls)} total")
        return sample
        
    except Exception as e:
        print(f"Error loading URLs: {e}")
        return []

def check_url_fast(url: str) -> Tuple[str, bool, int]:
    """Quick URL check with shorter timeout."""
    try:
        response = requests.head(url, timeout=3, allow_redirects=True)
        return url, response.status_code == 200, response.status_code
    except:
        return url, False, 0

def main():
    """Check a sample of URLs to assess data quality."""
    sample_urls = load_sample_urls("data/turnovers.csv", 50)
    
    if not sample_urls:
        return
    
    print("Checking URLs...")
    
    valid_count = 0
    results = []
    
    # Use thread pool for faster checking
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_url_fast, url): url for url in sample_urls}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url, is_valid, status_code = future.result()
            results.append((url, is_valid, status_code))
            
            if is_valid:
                valid_count += 1
                print(f"✓ Valid: {url[:60]}...")
            else:
                print(f"✗ Invalid ({status_code}): {url[:60]}...")
    
    print(f"\nSample Results:")
    print(f"Valid: {valid_count}/{len(sample_urls)} ({valid_count/len(sample_urls)*100:.1f}%)")
    
    if valid_count == 0:
        print("\nAll sampled URLs are invalid. The entire dataset appears to be expired.")
        print("Discord CDN links typically expire after some time.")
        print("\nRecommendation: You'll need fresh video URLs to replace this dataset.")
    elif valid_count < len(sample_urls) * 0.5:
        print(f"\nMost URLs are invalid. Running full cleanup would be recommended.")
    else:
        print(f"\nMost URLs are valid. Running full cleanup would preserve {valid_count/len(sample_urls)*100:.1f}% of data.")

if __name__ == "__main__":
    main()