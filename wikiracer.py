import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

class WikiRacer:
    def __init__(self, start_url, end_url, max_depth=5):
        self.start_url = start_url
        self.end_url = end_url
        self.base_url = "https://en.wikipedia.org"
        self.visited = set()
        self.cache = {}
        self.max_depth = max_depth
    
    def get_links(self, url):
        if url in self.cache:
            return self.cache[url]

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find(id="bodyContent")
        links = set()

        if content:
            for link in content.find_all("a", href=True):
                href = link["href"]
                if href.startswith("/wiki/") and not ":" in href:
                    full_url = urljoin(self.base_url, href)
                    links.add(full_url)
            self.cache[url] = links
        return links
    
    def bfs_path(self):
        queue = deque([(self.start_url, [self.start_url])])
        self.visited.add(self.start_url)
        
        depth = 0

        while queue and depth < self.max_depth:
            depth += 1
            next_level = []
            print(f"\nProcessing depth level {depth} with {len(queue)} paths in queue...")
            futures = {}

            with ThreadPoolExecutor() as executor:
                for current_url, path in queue:
                    futures[executor.submit(self.get_links, current_url)] = (current_url, path)

                for future in as_completed(futures):
                    current_url, path = futures[future]
                    try:
                        links = future.result()
                    except Exception as e:
                        print(f"Error processing {current_url}: {e}")
                        continue

                    for link in links:
                        if link == self.end_url:
                            print("End page reached!")
                            return path + [link]
                        if link not in self.visited:
                            self.visited.add(link)
                            next_level.append((link, path + [link]))

            queue = deque(next_level)
            print(f"Depth level {depth} completed with {len(next_level)} new paths added.")
        
        print("No path found within depth limit.")
        return None

    def find_path(self):
        path = self.bfs_path()
        if path:
            print("\nPath found:")
            for step, link in enumerate(path, 1):
                print(f"{step}. {link}")
        else:
            print("No path found between the given Wikipedia pages.")


if __name__ == "__main__":
    start_page = "https://en.wikipedia.org/wiki/Battle_of_Cr%C3%A9cy"
    end_page = "https://en.wikipedia.org/wiki/Wehrmacht"
    
    racer = WikiRacer(start_page, end_page, max_depth=5)
    racer.find_path()
