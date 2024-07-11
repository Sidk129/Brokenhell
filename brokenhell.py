import requests
import argparse
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import concurrent.futures
import time


def get_links(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                links.append(full_url)
            return links
        else:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []


def check_link(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return url, response.status_code
    except requests.RequestException:
        return url, 0


def is_valid(url, base_domain):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and base_domain in parsed.netloc


def crawl_site(base_url, max_depth=2):
    visited = set()
    to_visit = [(base_url, 1)]
    links = []
    base_domain = urlparse(base_url).netloc

    while to_visit:
        url, depth = to_visit.pop(0)
        if url in visited or depth > max_depth:
            continue
        visited.add(url)
        print(f"Crawling {url}")
        current_links = get_links(url)
        links.extend(current_links)
        for link in current_links:
            if is_valid(link, base_domain) and link not in visited:
                to_visit.append((link, depth + 1))
    return links


def process_sites(urls):
    broken_links = []
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_link, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                url, status_code = future.result()
                if status_code == 0 or status_code >= 400:
                    broken_links.append((url, status_code))
                    print(f"Broken link found: {url} - HTTP status code: {status_code}")
            except Exception as e:
                print(f"Error checking link: {future_to_url[future]}, Error: {e}")
    end_time = time.time()
    processing_time = end_time - start_time
    return broken_links, processing_time


def save_output(output_file, broken_links):
    with open(output_file, 'w') as f:
        for link, status_code in broken_links:
            f.write(f"{link} - HTTP status code: {status_code}\n")
    print(f"Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Broken Links Checker")
    parser.add_argument('base_url', nargs='?', help="Base URL to start crawling")
    parser.add_argument('-d', '--depth', type=int, default=2,
                        help="Maximum depth for crawling (default: 2)")
    parser.add_argument('-o', '--output', metavar='output_file',
                        help="Output file to save broken links")
    parser.add_argument('-f', '--file', metavar='input_file',
                        help="File containing list of websites to check")
    
    args = parser.parse_args()

    if not args.base_url and not args.file:
        parser.error("Please provide either a base URL or an input file.")

    if args.file:
        try:
            with open(args.file, 'r') as f:
                websites = [line.strip() for line in f if line.strip()]
        except IOError as e:
            print(f"Error reading input file: {e}")
            return
    else:
        websites = crawl_site(args.base_url, args.depth)

    if not websites:
        print("No valid websites to process. Exiting.")
        return

    broken_links, processing_time = process_sites(websites)

    print(f"Processed {len(websites)} websites in {processing_time:.2f} seconds.")
    print(f"Found {len(broken_links)} broken links:")

    for link, status_code in broken_links:
        print(f"{link} - HTTP status code: {status_code}")

    if args.output:
        save_output(args.output, broken_links)


if __name__ == "__main__":
    main()
