# Document processing utilities - Extracted from enhanced_index.py
import os
import re
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Document processing service for content analysis"""
    
    @staticmethod
    def extract_text_from_content(content: str, content_type: str) -> str:
        """Extract text content from various file types (from enhanced_index.py)"""
        try:
            if content_type == 'application/json':
                data = json.loads(content)
                return json.dumps(data, indent=2)
            elif content_type == 'text/plain':
                return content
            elif content_type == 'text/csv':
                # Basic CSV processing
                lines = content.split('\n')
                return '\n'.join(lines[:10])  # First 10 lines for preview
            else:
                # For other types, return a preview
                return content[:1000] + "..." if len(content) > 1000 else content
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return content[:500] if content else ""
    
    @staticmethod
    def extract_metadata_from_content(content: str, filename: str) -> Dict[str, Any]:
        """Extract metadata from document content (from enhanced_index.py)"""
        metadata = {
            'word_count': len(content.split()) if content else 0,
            'character_count': len(content) if content else 0,
            'line_count': len(content.split('\n')) if content else 0,
            'file_extension': os.path.splitext(filename)[1].lower(),
            'has_email': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
            'has_phone': bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)),
            'has_url': bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)),
            'language_detected': 'en',  # Simplified - would use language detection library in production
            'keywords': DocumentProcessingService.extract_keywords(content),
            'entities': DocumentProcessingService.extract_entities(content)
        }
        return metadata
    
    @staticmethod
    def extract_keywords(content: str) -> List[str]:
        """Extract keywords from content (from enhanced_index.py)"""
        if not content:
            return []
        
        # Simple keyword extraction - in production, use NLP libraries
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top 10 most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]
    
    @staticmethod
    def extract_entities(content: str) -> Dict[str, List[str]]:
        """Extract entities from content (from enhanced_index.py)"""
        entities = {
            'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content),
            'phones': re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content),
            'urls': re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content),
            'dates': re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', content),
            'amounts': re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', content)
        }
        return entities
    
    @staticmethod
    def calculate_complexity_score(metadata: Dict[str, Any]) -> float:
        """Calculate document complexity score (from enhanced_index.py)"""
        score = 0.0
        
        # Word count factor
        word_count = metadata.get('word_count', 0)
        if word_count > 1000:
            score += 0.3
        elif word_count > 500:
            score += 0.2
        elif word_count > 100:
            score += 0.1
        
        # Entity richness
        entities = metadata.get('entities', {})
        entity_count = sum(len(v) for v in entities.values())
        if entity_count > 10:
            score += 0.3
        elif entity_count > 5:
            score += 0.2
        elif entity_count > 0:
            score += 0.1
        
        # Keyword diversity
        keywords = metadata.get('keywords', [])
        if len(keywords) > 10:
            score += 0.2
        elif len(keywords) > 5:
            score += 0.1
        
        # File type complexity
        file_ext = metadata.get('file_extension', '')
        if file_ext in ['.pdf', '.docx', '.pptx']:
            score += 0.2
        elif file_ext in ['.doc', '.xlsx']:
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
        """Validate file extension (from enhanced_app.py)"""
        if not filename:
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in allowed_extensions
    
    @staticmethod
    def get_file_hash(content: bytes) -> str:
        """Generate file hash for deduplication (from enhanced_app.py)"""
        import hashlib
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def get_file_type(filename: str) -> str:
        """Determine file type based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.pdf', '.doc', '.docx', '.txt']:
            return 'documents'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'images'
        elif ext in ['.mp4', '.avi', '.mov']:
            return 'videos'
        else:
            return 'other'
