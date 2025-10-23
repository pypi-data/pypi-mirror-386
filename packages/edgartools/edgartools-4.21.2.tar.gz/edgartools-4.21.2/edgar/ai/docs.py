"""
Programmatic access to EdgarTools documentation for AI agents.

Provides methods to retrieve, search, and query documentation content
from markdown files.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import re
import yaml


class Docs:
    """
    Programmatic access to EdgarTools documentation.

    Provides methods for AI agents to retrieve and query documentation:
    - .get(name) - Get complete document
    - .search(query) - Search across all docs
    - .section(name, section) - Get specific section
    - .list() - List available documents
    - .frontmatter(name) - Get YAML metadata

    Examples:
        >>> docs = Docs()
        >>> # Get complete guide
        >>> guide = docs.get("sec-analysis")
        >>>
        >>> # Search for content
        >>> results = docs.search("revenue")
        >>>
        >>> # Get specific section
        >>> quickstart = docs.section("sec-analysis", "Quick Start")
        >>>
        >>> # List all documents
        >>> available = docs.list()
        >>>
        >>> # Get metadata
        >>> meta = docs.frontmatter("sec-analysis")
    """

    def __init__(self):
        """Initialize Docs with path to content directory."""
        self._content_dir = Path(__file__).parent / "_content"
        if not self._content_dir.exists():
            raise RuntimeError(
                f"Documentation content directory not found: {self._content_dir}"
            )

    def get(self, name: str) -> str:
        """
        Get complete documentation content.

        Args:
            name: Document name (e.g., "sec-analysis", "objects", "workflows")

        Returns:
            Complete document content as string

        Raises:
            FileNotFoundError: If document doesn't exist

        Examples:
            >>> docs = Docs()
            >>> guide = docs.get("sec-analysis")
            >>> print(guide[:100])  # First 100 chars
        """
        doc_path = self._content_dir / f"{name}.md"
        if not doc_path.exists():
            raise FileNotFoundError(
                f"Document '{name}' not found. Available: {', '.join(self.list())}"
            )
        return doc_path.read_text()

    def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for query across all documentation.

        Args:
            query: Search term or phrase
            case_sensitive: Whether to match case exactly (default: False)

        Returns:
            List of matches with document name, section, and context

        Examples:
            >>> docs = Docs()
            >>> results = docs.search("revenue")
            >>> for result in results:
            ...     print(f"{result['document']}: {result['section']}")
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        for doc_file in self._content_dir.glob("*.md"):
            doc_name = doc_file.stem
            content = doc_file.read_text()

            # Split into sections
            sections = self._split_sections(content)

            for section_name, section_content in sections.items():
                if re.search(query, section_content, flags):
                    # Extract context around match
                    match = re.search(query, section_content, flags)
                    if match:
                        start = max(0, match.start() - 50)
                        end = min(len(section_content), match.end() + 50)
                        context = section_content[start:end]

                        results.append({
                            'document': doc_name,
                            'section': section_name,
                            'context': context.strip(),
                            'match_position': match.start()
                        })

        return results

    def section(self, name: str, section: str) -> str:
        """
        Get specific section from a document.

        Args:
            name: Document name (e.g., "sec-analysis")
            section: Section title (e.g., "Quick Start")

        Returns:
            Section content as string

        Raises:
            FileNotFoundError: If document doesn't exist
            ValueError: If section not found

        Examples:
            >>> docs = Docs()
            >>> quickstart = docs.section("sec-analysis", "Quick Start")
        """
        content = self.get(name)
        sections = self._split_sections(content)

        # Try exact match first
        if section in sections:
            return sections[section]

        # Try case-insensitive match
        section_lower = section.lower()
        for sec_name, sec_content in sections.items():
            if sec_name.lower() == section_lower:
                return sec_content

        available = ', '.join(sections.keys())
        raise ValueError(
            f"Section '{section}' not found in '{name}'. "
            f"Available sections: {available}"
        )

    def list(self) -> List[str]:
        """
        List all available documents.

        Returns:
            List of document names (without .md extension)

        Examples:
            >>> docs = Docs()
            >>> available = docs.list()
            >>> print(available)
            ['sec-analysis', 'objects', 'workflows', 'readme']
        """
        return sorted([f.stem for f in self._content_dir.glob("*.md")])

    def frontmatter(self, name: str) -> Dict[str, Any]:
        """
        Get YAML frontmatter metadata from document.

        Args:
            name: Document name (e.g., "sec-analysis")

        Returns:
            Dictionary with frontmatter data (name, description, etc.)

        Raises:
            FileNotFoundError: If document doesn't exist
            ValueError: If document has no frontmatter

        Examples:
            >>> docs = Docs()
            >>> meta = docs.frontmatter("sec-analysis")
            >>> print(meta['name'])
            'SEC Filing Analysis'
            >>> print(meta['description'])
        """
        content = self.get(name)

        if not content.startswith("---\n"):
            raise ValueError(f"Document '{name}' has no YAML frontmatter")

        parts = content.split("---\n", 2)
        if len(parts) < 3:
            raise ValueError(f"Document '{name}' has invalid frontmatter structure")

        return yaml.safe_load(parts[1])

    def _split_sections(self, content: str) -> Dict[str, str]:
        """
        Split document into sections by markdown headers.

        Args:
            content: Document content

        Returns:
            Dictionary mapping section names to content
        """
        # Remove frontmatter if present
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                content = parts[2]

        sections = {}
        current_section = "Introduction"
        current_content = []

        for line in content.split('\n'):
            # Check for markdown header (## or higher)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections
