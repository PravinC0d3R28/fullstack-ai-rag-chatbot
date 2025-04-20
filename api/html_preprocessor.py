from bs4 import BeautifulSoup
import re
import os
from typing import Optional, List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLPreprocessor:
    """
    A class to preprocess HTML documents before they're added to the vector database.
    This helps to remove unnecessary elements, extract meaningful content,
    and reduce redundancy in the stored data.
    """
    
    def __init__(self, min_text_length: int = 50):
        """
        Initialize the HTMLPreprocessor.
        
        Args:
            min_text_length: Minimum character length for a text section to be considered meaningful
        """
        self.min_text_length = min_text_length
        # Track document stats for logging
        self.stats = {
            "original_size": 0,
            "processed_size": 0,
            "removed_elements": 0
        }
    
    def preprocess_html(self, html_content: str, file_path: Optional[str] = None) -> str:
        """
        Clean and preprocess HTML content.
        
        Args:
            html_content: The raw HTML content
            file_path: Path to the original file (for logging)
            
        Returns:
            Cleaned and preprocessed text content
        """
        self.stats = {
            "original_size": len(html_content),
            "processed_size": 0,
            "removed_elements": 0
        }
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove elements that typically don't contain useful text
            self._remove_unwanted_elements(soup)
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Combine title and content
            processed_text = ""
            if title:
                processed_text += f"# {title}\n\n"
            
            processed_text += main_content
            
            # Post-processing to clean up text
            processed_text = self._post_process_text(processed_text)
            
            self.stats["processed_size"] = len(processed_text)
            
            # Log stats
            if file_path:
                logger.info(f"Preprocessed {os.path.basename(file_path)}: "
                          f"Original size: {self.stats['original_size']} chars, "
                          f"Processed size: {self.stats['processed_size']} chars, "
                          f"Size reduction: {(1 - self.stats['processed_size'] / self.stats['original_size']) * 100:.2f}%, "
                          f"Removed elements: {self.stats['removed_elements']}")
            
            return processed_text
        
        except Exception as e:
            logger.error(f"Error preprocessing HTML content: {str(e)}")
            # Return original content if processing fails
            return self._extract_text_fallback(html_content)
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """
        Remove unwanted elements from the HTML.
        
        Args:
            soup: BeautifulSoup object
        """
        # List of tags to remove entirely
        tags_to_remove = [
            'script', 'style', 'noscript', 'iframe', 'svg', 'path', 'meta',
            'link', 'head', 'footer', 'nav', 'header', 'aside'
        ]
        
        # Specific classes/IDs that likely contain navigation, ads, etc.
        selectors_to_remove = [
            '.menu', '.navigation', '.nav', '.sidebar', '.footer', '.header',
            '.banner', '.advertisement', '.ad', '.cookie', '#menu', '#navigation',
            '#nav', '#sidebar', '#footer', '#header', '.social', '.share',
            '.copyright', '.terms', '.privacy', '.modal', '.popup'
        ]
        
        # Remove elements by tag
        for tag in tags_to_remove:
            for element in soup.find_all(tag):
                element.decompose()
                self.stats["removed_elements"] += 1
        
        # Remove elements by selector
        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()
                self.stats["removed_elements"] += 1
        
        # Remove all empty divs
        for div in soup.find_all('div', recursive=True):
            if not div.get_text(strip=True):
                div.decompose()
                self.stats["removed_elements"] += 1
        
        # Remove all comments
        for comment in soup.find_all(text=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
            comment.extract()
            self.stats["removed_elements"] += 1

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the title from the HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Title text
        """
        title = ""
        # Try to get title from h1 first
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        # If no h1, try title tag
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
            # Clean up title - remove website name
            if '-' in title:
                title = title.split('-')[0].strip()
            elif '|' in title:
                title = title.split('|')[0].strip()
        
        return title
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from the HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Main content text
        """
        # First check for main content containers
        main_candidates = []
        
        # Check for main tag
        main_tag = soup.find('main')
        if main_tag:
            main_candidates.append(main_tag)
        
        # Check for article tag
        article_tags = soup.find_all('article')
        if article_tags:
            main_candidates.extend(article_tags)
        
        # Check for common content selectors
        content_selectors = [
            '.content', '#content', '.main-content', '#main-content',
            '.article', '#article', '.post', '#post', '.page-content',
            '#page-content', '.entry-content', '#entry-content',
            '.container', '.wrapper'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_candidates.extend(elements)
        
        # Process main candidates to extract meaningful text sections
        content_sections = []
        
        if main_candidates:
            # Process each main candidate
            for candidate in main_candidates:
                sections = self._extract_text_sections(candidate)
                if sections:
                    content_sections.extend(sections)
        else:
            # If no main candidates found, use the body
            body = soup.find('body')
            if body:
                sections = self._extract_text_sections(body)
                if sections:
                    content_sections.extend(sections)
        
        # If still no content, try to get all paragraphs as a fallback
        if not content_sections:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > self.min_text_length:
                    content_sections.append(text)
        
        # Combine all sections with newlines
        content = '\n\n'.join(content_sections)
        
        return content
    
    def _extract_text_sections(self, element: BeautifulSoup) -> List[str]:
        """
        Extract meaningful text sections from an element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            List of text sections
        """
        sections = []
        
        # First try to get structured content with headings
        current_section = []
        current_heading = None
        
        # Process all children
        for child in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table', 'div'], recursive=True):
            # Skip empty elements
            if not child.get_text(strip=True):
                continue
                
            # Check if it's a heading
            if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # If we have content from previous heading, add it
                if current_heading and current_section:
                    sections.append(f"{current_heading}\n{' '.join(current_section)}")
                    current_section = []
                
                # Start new section with this heading
                current_heading = child.get_text(strip=True)
            
            # For paragraphs and other content
            elif child.name in ['p', 'ul', 'ol', 'table']:
                text = child.get_text(strip=True)
                if text:
                    # Clean up excessive whitespace
                    text = re.sub(r'\s+', ' ', text)
                    current_section.append(text)
            
            # For divs, only include if they contain direct text (not just through children)
            elif child.name == 'div':
                # Get direct text nodes
                direct_text = ''.join(child.find_all(text=True, recursive=False))
                if direct_text.strip():
                    # Clean up excessive whitespace
                    text = re.sub(r'\s+', ' ', direct_text.strip())
                    if len(text) > self.min_text_length:
                        current_section.append(text)
        
        # Add the last section if we have one
        if current_heading and current_section:
            sections.append(f"{current_heading}\n{' '.join(current_section)}")
        elif current_section:
            sections.append(' '.join(current_section))
        
        # If we didn't get structured content, try to get all text
        if not sections:
            text = element.get_text(strip=True)
            # Clean up excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            if len(text) > self.min_text_length:
                sections.append(text)
        
        return sections
    
    def _post_process_text(self, text: str) -> str:
        """
        Post-process text to clean it up.
        
        Args:
            text: Text to process
            
        Returns:
            Processed text
        """
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()
    
    def _extract_text_fallback(self, html_content: str) -> str:
        """
        Fallback method to extract text from HTML if BeautifulSoup processing fails.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Extracted text
        """
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def preprocess_file(self, file_path: str) -> str:
        """
        Preprocess an HTML file.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Preprocessed text
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self.preprocess_html(html_content, file_path)
        
        except Exception as e:
            logger.error(f"Error preprocessing file {file_path}: {str(e)}")
            return ""
    
    def identify_duplicate_content(self, documents: List[str]) -> Dict[str, List[int]]:
        """
        Identify duplicate/redundant content across documents.
        
        Args:
            documents: List of preprocessed document texts
            
        Returns:
            Dictionary mapping content hashes to document indices
        """
        content_map = {}
        
        for i, doc in enumerate(documents):
            # Split into paragraphs
            paragraphs = doc.split('\n\n')
            
            for paragraph in paragraphs:
                if len(paragraph) > self.min_text_length:
                    # Create a content hash
                    content_hash = paragraph.strip()
                    
                    if content_hash not in content_map:
                        content_map[content_hash] = []
                    
                    content_map[content_hash].append(i)
        
        # Filter to only duplicated content
        duplicates = {k: v for k, v in content_map.items() if len(v) > 1}
        
        return duplicates

def preprocess_html_folder(folder_path: str) -> List[Tuple[str, str]]:
    """
    Preprocess all HTML files in a folder.
    
    Args:
        folder_path: Path to the folder containing HTML files
        
    Returns:
        List of tuples with (file_path, preprocessed_content)
    """
    preprocessor = HTMLPreprocessor()
    results = []
    
    try:
        # Get all HTML files in the folder
        html_files = [f for f in os.listdir(folder_path) if f.endswith('.html')]
        logger.info(f"Found {len(html_files)} HTML files in {folder_path}")
        
        # Process each file
        for file_name in html_files:
            file_path = os.path.join(folder_path, file_name)
            processed_content = preprocessor.preprocess_file(file_path)
            
            if processed_content:
                results.append((file_path, processed_content))
        
        return results
    
    except Exception as e:
        logger.error(f"Error preprocessing folder {folder_path}: {str(e)}")
        return [] 