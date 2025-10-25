"""External content extractor for web URLs"""

import requests
import time
from typing import Optional, Union
from pathlib import Path
from urllib.parse import urlparse
from .base import ContentExtractor


class ExternalExtractor(ContentExtractor):
    """Extract content from web URLs"""

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None, use_browser: bool = True):
        self.timeout = timeout
        self.user_agent = user_agent or "pantsonfire/0.1.0 (https://github.com/seanmcdonald/pantsonfire)"
        self.use_browser = use_browser
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
        self.browser_driver = None

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
                print(f"❌ Failed to fetch {url}: HTTP {response.status_code}")
                return None

            content_type = response.headers.get('content-type', '').lower()

            if 'text/html' in content_type:
                content = self._extract_html(response.text, url)
                # If traditional extraction failed or returned minimal content and browser is enabled, try browser automation
                if (content is None or len(content.strip()) < 100) and self.use_browser:
                    print(f"🔄 Traditional extraction failed or returned minimal content, trying browser automation for {url}...")
                    browser_content = self._extract_with_browser(url)
                    if browser_content and len(browser_content.strip()) > 50:
                        return browser_content
                return content
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

    def _extract_with_browser(self, url: str) -> Optional[str]:
        """
        Extract content using browser automation for JavaScript-heavy sites.

        Args:
            url: Web URL to extract from

        Returns:
            Extracted text content, or None if failed
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException, WebDriverException
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            print("⚠️  Selenium not installed, skipping browser automation")
            return None

        driver = None
        try:
            # Set up headless Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.user_agent}")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Speed up loading

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Navigate to the page
            driver.get(url)

            # Wait for page to load (basic wait)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for dynamic content (up to 15 seconds)
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
            except TimeoutException:
                pass  # Continue anyway

            # Extract text content using JavaScript
            text_content = driver.execute_script("""
                // Remove unwanted elements
                const elementsToRemove = document.querySelectorAll('script, style, nav, header, footer, aside, noscript, .ads, .advertisement, .sidebar');
                elementsToRemove.forEach(el => el.remove());

                // Try to find main content
                const contentSelectors = [
                    'main',
                    '[role="main"]',
                    '.content',
                    '.post-content',
                    '.entry-content',
                    '.article-content',
                    '#content',
                    '#main',
                    '.markdown-body',
                    '.doc-content',
                    'article',
                    '.post',
                    '.blog-post'
                ];

                let mainContent = null;
                for (const selector of contentSelectors) {
                    mainContent = document.querySelector(selector);
                    if (mainContent && mainContent.textContent.trim().length > 100) {
                        break;
                    }
                }

                // Fallback to body if no main content found
                if (!mainContent || mainContent.textContent.trim().length < 100) {
                    mainContent = document.body;
                }

                // Extract clean text
                function extractText(element) {
                    const cloned = element.cloneNode(true);
                    const elementsToRemove = cloned.querySelectorAll('script, style, nav, header, footer, aside, noscript');
                    elementsToRemove.forEach(el => el.remove());

                    return cloned.textContent || cloned.innerText || '';
                }

                return extractText(mainContent);
            """)

            # Clean up the text
            if text_content:
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                cleaned_text = '\n\n'.join(lines)
                return cleaned_text

            return None

        except Exception as e:
            print(f"❌ Browser extraction failed: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

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
