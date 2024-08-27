import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_clean_url(url):
    """
    Remove query parameters and fragments from a URL.
    """
    parsed_url = urlparse(url)
    clean_url = urlunparse(parsed_url._replace(query='', fragment=''))
    return clean_url

def check_url_reachability(url):
    """
    Check if a URL is reachable.
    """
    try:
        response = requests.head(url, timeout=5)
        response.raise_for_status()
        return url, True
    except requests.exceptions.RequestException:
        return url, False

def is_domain_allowed(url, allowed_domains):
    """
    Check if the URL's domain is in the list of allowed domains.
    """
    parsed_url = urlparse(url)
    return any(parsed_url.netloc.endswith(domain) for domain in allowed_domains)

def get_urls_from_page(url, level, max_urls, allowed_domains):
    # If level is 0, check the input URL's reachability and return accordingly
    if level == 0:
        reachable_urls = set()
        unreachable_urls = set()

        if is_domain_allowed(url, allowed_domains or []):
            clean_url = get_clean_url(url)
            _, is_reachable = check_url_reachability(clean_url)
            if is_reachable:
                reachable_urls.add(clean_url)
            else:
                unreachable_urls.add(clean_url)
        
        return reachable_urls, unreachable_urls

    if level < 1 or max_urls < 1:
        return set(), set()

    if allowed_domains is None:
        allowed_domains = []

    reachable_urls = set()
    unreachable_urls = set()

    try:
        # Fetch the HTML content of the page
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all anchor tags with href attribute
        urls_to_check = set()
        for anchor in soup.find_all('a', href=True):
            if len(urls_to_check) >= max_urls:
                break
            # Convert relative URLs to absolute URLs
            link = urljoin(url, anchor['href'])
            # Clean the URL to remove query params and fragments
            clean_link = get_clean_url(link)
            
            # Check if the URL belongs to an allowed domain
            if is_domain_allowed(clean_link, allowed_domains):
                urls_to_check.add(clean_link)
        
        # Check reachability using multiple threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_url_reachability, link) for link in urls_to_check]
            for future in as_completed(futures):
                link, is_reachable = future.result()
                if is_reachable:
                    reachable_urls.add(link)
                else:
                    unreachable_urls.add(link)
                if len(reachable_urls) + len(unreachable_urls) >= max_urls:
                    break

        # If level is more than 1 and max_urls not reached, get URLs from the linked pages
        if level > 1 and len(reachable_urls) + len(unreachable_urls) < max_urls:
            for link in list(reachable_urls):
                sub_reachable, sub_unreachable = get_urls_from_page(link, level-1, max_urls - len(reachable_urls) - len(unreachable_urls), allowed_domains)
                reachable_urls.update(sub_reachable)
                unreachable_urls.update(sub_unreachable)
                if len(reachable_urls) + len(unreachable_urls) >= max_urls:
                    break
        
        return reachable_urls, unreachable_urls
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return set(), set()

# # Example usage
# allowed_domains = ["example.com", "anotherdomain.com"]
# reachable_urls, unreachable_urls = get_urls_from_page("https://example.com", level=0, max_urls=50, allowed_domains=allowed_domains)

# # Returning the results as a tuple
# result = (list(reachable_urls), list(unreachable_urls))
