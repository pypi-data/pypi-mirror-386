"""
Web scraping capabilities for pantsonfire.
Provides crawling functionality to discover related content and issues.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Optional
from pathlib import Path
import time
import re

from .base import BaseContentExtractor
from ..config import Config


class WebScraper(BaseContentExtractor):
    """
    Web scraper for discovering related content and potential issues.
    """

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent
        })
        self.visited_urls: Set[str] = set()
        self.found_issues: List[Dict] = []

    def can_handle(self, source) -> bool:
        """Check if source is a web URL"""
        if isinstance(source, str):
            return source.startswith(('http://', 'https://'))
        return False

    def extract(self, source) -> Optional[str]:
        """Extract content from web URL (basic implementation)"""
        # This is a basic implementation - enhanced crawling is done separately
        return self._fetch_page_content(str(source))

    def crawl_for_similar_issues(
        self,
        start_urls: List[str],
        keywords: List[str],
        max_pages: int = 10
    ) -> Dict[str, str]:
        """
        Crawl websites to find pages with similar issues.

        Args:
            start_urls: URLs to start crawling from
            keywords: Keywords to search for (e.g., "get early access", "deprecated")
            max_pages: Maximum pages to crawl

        Returns:
            Dictionary of URL -> content for pages that match criteria
        """
        print(f"🕷️  Starting web crawl from {len(start_urls)} URLs...")
        print(f"🔍 Looking for keywords: {keywords}")

        results = {}
        to_visit = start_urls.copy()
        visited_count = 0

        while to_visit and visited_count < max_pages:
            current_url = to_visit.pop(0)

            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            visited_count += 1

            print(f"📄 Crawling: {current_url}")

            try:
                content = self._fetch_page_content(current_url)
                if not content:
                    continue

                # Check if page contains relevant keywords
                if self._contains_relevant_keywords(content, keywords):
                    results[current_url] = content
                    print(f"✅ Found relevant content: {current_url}")

                    # Extract links from this page for further crawling
                    if len(to_visit) < max_pages - visited_count:
                        new_links = self._extract_links(current_url, content)
                        # Only add links from the same domain
                        domain = urlparse(current_url).netloc
                        same_domain_links = [
                            link for link in new_links
                            if urlparse(link).netloc == domain and link not in self.visited_urls
                        ]
                        to_visit.extend(same_domain_links[:5])  # Limit to 5 new links per page

                time.sleep(1)  # Be respectful to servers

            except Exception as e:
                print(f"❌ Error crawling {current_url}: {e}")
                continue

        print(f"🏁 Crawl complete. Found {len(results)} relevant pages.")
        return results

    def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch and extract text content from a web page."""
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text = soup.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)

        except Exception as e:
            print(f"❌ Failed to fetch {url}: {e}")
            return None

    def _contains_relevant_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains relevant keywords."""
        content_lower = content.lower()

        # Check for exact keyword matches
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True

        # Check for related terms
        related_terms = [
            "deprecated", "outdated", "legacy", "obsolete",
            "no longer", "removed", "discontinued", "archived",
            "early access", "beta", "coming soon", "planned",
            "version", "update", "change", "migration"
        ]

        for term in related_terms:
            if term in content_lower:
                return True

        return False

    def _extract_links(self, base_url: str, content: str) -> List[str]:
        """Extract links from HTML content."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            links = []

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(base_url, href)

                # Only include HTTP/HTTPS links
                if absolute_url.startswith(('http://', 'https://')):
                    links.append(absolute_url)

            return links
        except Exception:
            return []

    def analyze_found_content(
        self,
        crawled_content: Dict[str, str],
        original_issue: str
    ) -> List[Dict]:
        """
        Analyze crawled content to find similar issues.

        Args:
            crawled_content: URL -> content dictionary from crawling
            original_issue: Description of the original issue

        Returns:
            List of potential issues found
        """
        issues = []

        for url, content in crawled_content.items():
            # Simple pattern matching for common issues
            content_lower = content.lower()

            # Check for "get early access" mentions
            if "get early access" in content_lower:
                issues.append({
                    "url": url,
                    "issue_type": "early_access_mention",
                    "description": "Page mentions 'Get Early Access' which may be outdated",
                    "evidence": "Contains 'get early access' text",
                    "severity": "medium"
                })

            # Check for version mentions that might be old
            version_matches = re.findall(r'v\d+\.\d+', content)
            if version_matches:
                issues.append({
                    "url": url,
                    "issue_type": "version_reference",
                    "description": f"Page references specific versions: {version_matches}",
                    "evidence": f"Found version strings: {version_matches}",
                    "severity": "low"
                })

            # Check for "coming soon" mentions
            if "coming soon" in content_lower:
                issues.append({
                    "url": url,
                    "issue_type": "coming_soon_mention",
                    "description": "Page mentions features as 'coming soon'",
                    "evidence": "Contains 'coming soon' text",
                    "severity": "low"
                })

            # Check for deprecated terms
            deprecated_terms = ["deprecated", "legacy", "obsolete", "no longer supported"]
            for term in deprecated_terms:
                if term in content_lower:
                    issues.append({
                        "url": url,
                        "issue_type": "deprecated_reference",
                        "description": f"Page mentions '{term}' content",
                        "evidence": f"Contains '{term}'",
                        "severity": "high"
                    })
                    break

        return issues
