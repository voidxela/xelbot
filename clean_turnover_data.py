"""
Script to clean turnover data by checking URL validity.
Removes any URLs that return errors and creates a cleaned CSV file.
"""

import requests
import re
import os
import time
from typing import List, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_turnover_urls(file_path: str) -> List[str]:
    """
    Load turnover URLs from the CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of URLs extracted from the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            content = file.read().strip()
            
            # Extract URLs from the format [URL]
            url_pattern = r'\[([^]]+)\]'
            urls = re.findall(url_pattern, content)
            
            # Filter out empty URLs and validate they're Discord CDN URLs
            valid_urls = [
                url.strip() for url in urls 
                if url.strip() and 'cdn.discordapp.com' in url
            ]
            
            logger.info(f"Loaded {len(valid_urls)} URLs from {file_path}")
            return valid_urls
            
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading URLs: {e}")
        return []

def check_url_status(url: str, timeout: int = 10) -> Tuple[str, bool, str]:
    """
    Check if a URL is accessible.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (url, is_valid, error_message)
    """
    try:
        # Use HEAD request to check without downloading the full file
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            return url, True, "OK"
        else:
            return url, False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return url, False, "Timeout"
    except requests.exceptions.ConnectionError:
        return url, False, "Connection Error"
    except requests.exceptions.RequestException as e:
        return url, False, f"Request Error: {str(e)}"
    except Exception as e:
        return url, False, f"Unknown Error: {str(e)}"

def check_all_urls(urls: List[str], delay: float = 0.5) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Check all URLs and return valid ones and invalid ones with reasons.
    
    Args:
        urls: List of URLs to check
        delay: Delay between requests in seconds
        
    Returns:
        Tuple of (valid_urls, invalid_urls_with_reasons)
    """
    valid_urls = []
    invalid_urls = []
    
    total_urls = len(urls)
    logger.info(f"Starting to check {total_urls} URLs...")
    
    for i, url in enumerate(urls, 1):
        logger.info(f"Checking URL {i}/{total_urls}: {url[:80]}...")
        
        url, is_valid, message = check_url_status(url)
        
        if is_valid:
            valid_urls.append(url)
            logger.info(f"✓ Valid: {message}")
        else:
            invalid_urls.append((url, message))
            logger.warning(f"✗ Invalid: {message}")
        
        # Add delay to be respectful to the server
        if i < total_urls:
            time.sleep(delay)
    
    logger.info(f"Check complete: {len(valid_urls)} valid, {len(invalid_urls)} invalid")
    return valid_urls, invalid_urls

def save_cleaned_data(valid_urls: List[str], output_path: str):
    """
    Save the cleaned URLs to a new CSV file.
    
    Args:
        valid_urls: List of valid URLs
        output_path: Path to save the cleaned file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            for url in valid_urls:
                file.write(f"[{url}] \n")
        
        logger.info(f"Saved {len(valid_urls)} valid URLs to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving cleaned data: {e}")

def save_invalid_report(invalid_urls: List[Tuple[str, str]], report_path: str):
    """
    Save a report of invalid URLs and their error reasons.
    
    Args:
        invalid_urls: List of (url, error_reason) tuples
        report_path: Path to save the report
    """
    try:
        with open(report_path, 'w', encoding='utf-8') as file:
            file.write("Invalid URLs Report\n")
            file.write("==================\n\n")
            
            for url, reason in invalid_urls:
                file.write(f"URL: {url}\n")
                file.write(f"Error: {reason}\n")
                file.write("-" * 80 + "\n")
        
        logger.info(f"Saved invalid URLs report to {report_path}")
        
    except Exception as e:
        logger.error(f"Error saving invalid URLs report: {e}")

def main():
    """
    Main function to clean the turnover data.
    """
    # File paths
    input_file = "data/turnovers.csv"
    output_file = "data/turnovers_cleaned.csv"
    report_file = "data/invalid_urls_report.txt"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    # Load URLs from the original file
    logger.info("Loading URLs from original file...")
    urls = load_turnover_urls(input_file)
    
    if not urls:
        logger.error("No URLs found in the input file")
        return
    
    # Check all URLs
    logger.info("Checking URL validity...")
    valid_urls, invalid_urls = check_all_urls(urls, delay=0.5)
    
    # Save results
    logger.info("Saving results...")
    save_cleaned_data(valid_urls, output_file)
    
    if invalid_urls:
        save_invalid_report(invalid_urls, report_file)
    
    # Print summary
    print("\n" + "="*60)
    print("CLEANUP SUMMARY")
    print("="*60)
    print(f"Original URLs: {len(urls)}")
    print(f"Valid URLs: {len(valid_urls)}")
    print(f"Invalid URLs: {len(invalid_urls)}")
    print(f"Success Rate: {len(valid_urls)/len(urls)*100:.1f}%")
    print(f"\nCleaned data saved to: {output_file}")
    
    if invalid_urls:
        print(f"Invalid URLs report saved to: {report_file}")
    
    print("\nTo use the cleaned data, update your bot to use the cleaned file:")
    print(f"mv {output_file} {input_file}")

if __name__ == "__main__":
    main()