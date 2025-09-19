"""
Technical Terms Dictionary and Correction
Handles common programming terms that get misheard in Spanish context
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Common technical terms and their Spanish misinterpretations
TECHNICAL_CORRECTIONS = {
    # English terms commonly misheard in Spanish
    'trinme': 'README',
    'trime': 'README',
    'ridmi': 'README',
    'redmi': 'README',
    'rid me': 'README',
    'read me': 'README',

    # Git related
    'git jab': 'GitHub',
    'guitjab': 'GitHub',
    'guit': 'git',
    'comit': 'commit',
    'pul': 'pull',
    'puch': 'push',
    'bransh': 'branch',
    'branch': 'branch',  # Keep as is

    # Programming terms
    'faison': 'Python',
    'paiton': 'Python',
    'piton': 'Python',
    'yasón': 'JSON',
    'yeison': 'JSON',
    'eich ti eme ele': 'HTML',
    'ce ese ese': 'CSS',
    'api': 'API',
    'a pi ai': 'API',

    # Common files
    'pac-age': 'package',
    'packash': 'package',
    'packash.yasón': 'package.json',
    'packash.json': 'package.json',
    'noud modules': 'node_modules',
    'nod modules': 'node_modules',
    'requaierments': 'requirements',
    'requeriments': 'requirements',
    'requairements': 'requirements',

    # Frameworks
    'riact': 'React',
    'riac': 'React',
    'angiular': 'Angular',
    'viu': 'Vue',
    'diango': 'Django',
    'flask': 'Flask',

    # Commands
    'enpiem': 'npm',
    'en pi eme': 'npm',
    'pip': 'pip',
    'pib': 'pip',
    'instal': 'install',
    'instol': 'install',

    # Database
    'escuel': 'SQL',
    'es cu ele': 'SQL',
    'posgrés': 'PostgreSQL',
    'postgre': 'PostgreSQL',
    'mongodivi': 'MongoDB',
    'mongo divi': 'MongoDB',

    # Common English words in tech
    'dita': 'data',
    'deita': 'data',
    'sérver': 'server',
    'claud': 'cloud',
    'claund': 'cloud',
    'douker': 'Docker',
    'doker': 'Docker',
}

# Patterns for contextual corrections
CONTEXTUAL_PATTERNS = [
    # When talking about documentation
    (r'\b(actualizar|update|cambiar|change)\s+(el\s+)?(trinme|trime|ridmi|redmi)\b', r'\1 \2README'),
    (r'\b(archivo|file)\s+(trinme|trime|ridmi|redmi)\b', r'\1 README'),

    # When talking about git
    (r'\b(hacer|make|create)\s+(un\s+)?(comit|commit)\b', r'\1 \2commit'),
    (r'\b(subir|upload|push)\s+(a\s+)?(git jab|guitjab)\b', r'\1 \2GitHub'),
    (r'\b(nuevo|new)\s+(bransh)\s+en\s+(git jab)\b', r'\1 branch en GitHub'),

    # Package management
    (r'\b(enpiem|en pi eme)\s+(instal|instol)\b', r'npm install'),
    (r'\b(pib|pip)\s+(instal|instol)\b', r'pip install'),
    (r'\b(pib|pip)\s+(instal|instol)\s+(requaierments|requeriments|requairements)\b', r'pip install requirements'),

    # File extensions and specific files
    (r'\bpackash\.(yasón|yeison|json)\b', r'package.json'),
    (r'\b(\w+)\.(yasón|yeison)\b', r'\1.json'),
    (r'\b(\w+)\.pi\b', r'\1.py'),
    (r'\b(\w+)\.yei ese\b', r'\1.js'),
    (r'\brequaierments\.txt\b', r'requirements.txt'),
]

class TechnicalTermsProcessor:
    """Processes text to correct technical terms misheard in Spanish context"""

    def __init__(self):
        self.corrections = TECHNICAL_CORRECTIONS.copy()
        self.patterns = CONTEXTUAL_PATTERNS.copy()

    def add_custom_term(self, misheard: str, correct: str):
        """Add a custom technical term correction"""
        self.corrections[misheard.lower()] = correct

    def process_text(self, text: str) -> str:
        """Process text to fix technical terms"""
        if not text:
            return text

        original_text = text
        processed = text

        # Apply contextual pattern replacements first
        for pattern, replacement in self.patterns:
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Then apply word-by-word corrections
        words = processed.split()
        corrected_words = []

        for word in words:
            # Check if word (lowercase) is in corrections
            lower_word = word.lower()

            # Preserve punctuation
            prefix = ""
            suffix = ""
            clean_word = word

            # Extract punctuation
            if word and not word[-1].isalnum():
                suffix = word[-1]
                clean_word = word[:-1]
                lower_word = clean_word.lower()

            if lower_word in self.corrections:
                corrected = self.corrections[lower_word]
                corrected_words.append(prefix + corrected + suffix)
                logger.debug(f"Corrected: '{word}' -> '{corrected}'")
            else:
                corrected_words.append(word)

        result = ' '.join(corrected_words)

        # Final cleanup - fix spacing issues
        result = re.sub(r'\s+', ' ', result)  # Multiple spaces to single
        result = re.sub(r'\s+([.,;!?])', r'\1', result)  # Remove space before punctuation

        if result != original_text:
            logger.info(f"Technical terms corrected: '{original_text[:30]}...' -> '{result[:30]}...'")

        return result

    def detect_code_context(self, text: str) -> bool:
        """Detect if the text is likely discussing code/technical topics"""
        code_indicators = [
            'código', 'code', 'programa', 'function', 'función',
            'archivo', 'file', 'carpeta', 'folder', 'directorio',
            'instalar', 'install', 'ejecutar', 'run', 'comando',
            'error', 'bug', 'debug', 'test', 'prueba'
        ]

        lower_text = text.lower()
        return any(indicator in lower_text for indicator in code_indicators)

    def suggest_corrections(self, text: str) -> List[Tuple[str, str]]:
        """Suggest possible corrections without applying them"""
        suggestions = []
        words = text.split()

        for word in words:
            lower_word = word.lower().strip('.,;!?')

            # Check for close matches (within 2 character edits)
            for misheard, correct in self.corrections.items():
                if self._is_similar(lower_word, misheard):
                    suggestions.append((word, correct))

        return suggestions

    def _is_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are similar (for fuzzy matching)"""
        # Simple edit distance check
        if abs(len(word1) - len(word2)) > 2:
            return False

        # Check if they share most characters
        common = sum(1 for c in word1 if c in word2)
        return common >= min(len(word1), len(word2)) - 2

# Global instance
_technical_processor = None

def get_technical_processor() -> TechnicalTermsProcessor:
    """Get or create the technical terms processor"""
    global _technical_processor
    if _technical_processor is None:
        _technical_processor = TechnicalTermsProcessor()
    return _technical_processor

def process_technical_terms(text: str) -> str:
    """Quick function to process technical terms in text"""
    processor = get_technical_processor()
    return processor.process_text(text)