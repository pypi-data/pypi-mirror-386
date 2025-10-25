"""Internal content extractor for local files and directories"""

import os
import json
from typing import Optional, Union
from pathlib import Path
from .base import ContentExtractor


class InternalExtractor(ContentExtractor):
    """Extract content from local files and directories"""

    def extract(self, source: Union[str, Path]) -> Optional[str]:
        """Extract content from local source"""
        path = Path(source)

        if path.is_file():
            return self._extract_file(path)
        elif path.is_dir():
            return self._extract_directory(path)
        else:
            # Try as relative path from current directory
            try:
                if os.path.isfile(source):
                    return self._extract_file(Path(source))
                elif os.path.isdir(source):
                    return self._extract_directory(Path(source))
            except:
                pass

        return None

    def _extract_file(self, file_path: Path) -> Optional[str]:
        """Extract content from a single file"""
        try:
            # Handle different file types
            if file_path.suffix.lower() in ['.md', '.markdown']:
                return self._extract_markdown(file_path)
            elif file_path.suffix.lower() == '.json':
                return self._extract_json(file_path)
            elif file_path.suffix.lower() in ['.txt', '.rst']:
                return file_path.read_text(encoding='utf-8')
            elif file_path.suffix.lower() in ['.html', '.htm']:
                return self._extract_html(file_path)
            else:
                # Try to read as text
                try:
                    return file_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    return None
        except Exception as e:
            print(f"Failed to extract from {file_path}: {e}")
            return None

    def _extract_directory(self, dir_path: Path) -> Optional[str]:
        """Extract content from a directory (concatenate all readable files)"""
        content_parts = []

        # Common documentation files to prioritize
        priority_files = ['README.md', 'readme.md', 'index.md', 'docs.md']

        # First, try priority files
        for filename in priority_files:
            filepath = dir_path / filename
            if filepath.exists():
                content = self._extract_file(filepath)
                if content:
                    content_parts.append(f"# {filename}\n\n{content}")

        # Then extract from all other markdown files
        for file_path in dir_path.rglob('*.md'):
            if file_path.name not in priority_files:
                content = self._extract_file(file_path)
                if content:
                    content_parts.append(f"# {file_path.relative_to(dir_path)}\n\n{content}")

        if content_parts:
            return "\n\n---\n\n".join(content_parts)

        # Fallback: try to extract from any text files
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.rst']:
                content = self._extract_file(file_path)
                if content:
                    content_parts.append(content)

        return "\n\n".join(content_parts) if content_parts else None

    def _extract_markdown(self, file_path: Path) -> str:
        """Extract and clean markdown content"""
        content = file_path.read_text(encoding='utf-8')

        # Basic cleaning: remove frontmatter if present
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]

        return content.strip()

    def _extract_json(self, file_path: Path) -> Optional[str]:
        """Extract readable content from JSON files"""
        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))

            # If it's a Mintlify-style config or content
            if isinstance(data, dict):
                content_parts = []

                # Extract navigation/pages if present
                if 'navigation' in data:
                    content_parts.append("Navigation:")
                    for item in data['navigation']:
                        if isinstance(item, dict) and 'group' in item:
                            content_parts.append(f"- {item['group']}")
                            if 'pages' in item:
                                for page in item['pages']:
                                    content_parts.append(f"  - {page}")

                # Extract other relevant fields
                for key in ['description', 'content', 'body']:
                    if key in data and isinstance(data[key], str):
                        content_parts.append(f"{key.title()}: {data[key]}")

                return "\n".join(content_parts) if content_parts else str(data)

        except Exception as e:
            print(f"Failed to parse JSON {file_path}: {e}")

        return None

    def _extract_html(self, file_path: Path) -> Optional[str]:
        """Extract readable text from HTML files"""
        try:
            from bs4 import BeautifulSoup

            content = file_path.read_text(encoding='utf-8')
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            print(f"Failed to extract HTML from {file_path}: {e}")
            return None

    def can_handle(self, source: Union[str, Path]) -> bool:
        """Check if source is a local file or directory"""
        path = Path(source)
        return path.exists() or os.path.exists(source)
