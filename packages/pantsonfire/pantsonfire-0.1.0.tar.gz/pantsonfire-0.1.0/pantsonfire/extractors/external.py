"""External content extractor for web URLs"""

import requests
import time
from typing import Optional, Union
from pathlib import Path
from urllib.parse import urlparse
from .base import ContentExtractor


class ExternalExtractor(ContentExtractor):
    """Extract content from web URLs"""

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.user_agent = user_agent or "pantsonfire/0.1.0 (https://github.com/seanmcdonald/pantsonfire)"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def extract(self, source: Union[str, Path]) -> Optional[str]:
        """Extract content from web URL or GitHub repo"""
        url = str(source)

        # Handle GitHub repositories
        if self._is_github_repo(url):
            return self._extract_github_repo(url)

        if not self._is_url(url):
            return None

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                print(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None

            content_type = response.headers.get('content-type', '').lower()

            if 'text/html' in content_type:
                return self._extract_html(response.text, url)
            elif 'application/json' in content_type:
                return self._extract_json(response.text, url)
            elif 'text/markdown' in content_type or url.endswith('.md'):
                return response.text
            elif 'text/plain' in content_type:
                return response.text
            else:
                # Try to extract text from HTML anyway
                return self._extract_html(response.text, url)

        except Exception as e:
            print(f"Failed to extract from {url}: {e}")
            return None

    def _extract_html(self, html_content: str, url: str) -> Optional[str]:
        """Extract readable text from HTML content"""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
                element.extract()

            # Try to find main content area
            content_selectors = [
                'main',
                '[role="main"]',
                '.content',
                '.post-content',
                '.entry-content',
                '.article-content',
                '#content',
                '#main',
                '.markdown-body',  # GitHub/GitLab style
                '.doc-content',    # Documentation sites
            ]

            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                # Fallback to body
                main_content = soup.body or soup

            # Extract text
            text = main_content.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n\n'.join(lines)

            return text

        except Exception as e:
            print(f"Failed to extract HTML content: {e}")
            return None

    def _extract_json(self, json_content: str, url: str) -> Optional[str]:
        """Extract readable content from JSON responses"""
        try:
            import json
            data = json.loads(json_content)

            # Handle common API response formats
            if isinstance(data, dict):
                content_parts = []

                # Extract relevant fields
                text_fields = ['content', 'body', 'description', 'text', 'markdown', 'html']
                for field in text_fields:
                    if field in data and isinstance(data[field], str):
                        content_parts.append(data[field])

                # Handle nested content (e.g., GitHub API)
                if 'items' in data and isinstance(data['items'], list):
                    for item in data['items'][:5]:  # Limit to first 5 items
                        if isinstance(item, dict):
                            for field in text_fields:
                                if field in item and isinstance(item[field], str):
                                    content_parts.append(item[field])

                return '\n\n'.join(content_parts) if content_parts else str(data)

        except Exception as e:
            print(f"Failed to extract JSON content: {e}")

        return None

    def _is_url(self, source: str) -> bool:
        """Check if source is a valid URL"""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _is_github_repo(self, url: str) -> bool:
        """Check if URL is a GitHub repository"""
        return 'github.com' in url and '/blob/' not in url and '/tree/' not in url

    def _extract_github_repo(self, url: str) -> Optional[str]:
        """Extract content from GitHub repository by fetching README and key docs"""
        try:
            # Extract owner/repo from URL
            parts = url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return None
            owner, repo = parts[0], parts[1]

            # Try to fetch README.md first
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
            response = self.session.get(readme_url, timeout=self.timeout)

            content_parts = []

            if response.status_code == 200:
                content_parts.append(f"# README.md\n\n{response.text}")

            # Try to fetch docs if they exist
            docs_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/docs/README.md"
            response = self.session.get(docs_url, timeout=self.timeout)
            if response.status_code == 200:
                content_parts.append(f"# docs/README.md\n\n{response.text}")

            # Try API docs
            api_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/docs/api.md"
            response = self.session.get(api_url, timeout=self.timeout)
            if response.status_code == 200:
                content_parts.append(f"# API Documentation\n\n{response.text}")

            # Get repository information from GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(api_url, timeout=self.timeout)
            if response.status_code == 200:
                repo_data = response.json()
                repo_info = f"""
# Repository Information

**Name**: {repo_data.get('name', 'Unknown')}
**Description**: {repo_data.get('description', 'No description')}
**Stars**: {repo_data.get('stargazers_count', 0)}
**Language**: {repo_data.get('language', 'Unknown')}
**Last Updated**: {repo_data.get('updated_at', 'Unknown')}

**Topics**: {', '.join(repo_data.get('topics', []))}
"""
                content_parts.insert(0, repo_info)

            return "\n\n---\n\n".join(content_parts) if content_parts else None

        except Exception as e:
            print(f"Failed to extract from GitHub repo {url}: {e}")
            return None

    def can_handle(self, source: Union[str, Path]) -> bool:
        """Check if source is a web URL or GitHub repo"""
        source_str = str(source)
        return self._is_url(source_str) or self._is_github_repo(source_str)
