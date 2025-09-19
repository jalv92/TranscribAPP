"""
Simple text processing fallback when LLM is not available or too slow
"""
import re
import logging

logger = logging.getLogger(__name__)


class SimpleTextProcessor:
    """Fallback text processor using regex and rules"""

    def __init__(self):
        # Spanish filler words to remove
        self.spanish_fillers = [
            r'\b(este|eh|mmm|um|uhm|ah|oh|bueno)\b',
            r'\s+',  # Multiple spaces
            r'^\s+|\s+$'  # Trim
        ]

        # Common Spanish-English translation fixes
        self.translation_fixes = {
            # Common mistranslations
            'the the': 'the',
            'a a': 'a',
            'is is': 'is',
            # Capitalization
            r'^(\w)': lambda m: m.group(1).upper(),
            # Period at end if missing
            r'([a-zA-Z])$': r'\1.'
        }

    def clean_spanish_text(self, text: str) -> str:
        """Remove filler words and clean Spanish text"""
        try:
            cleaned = text.lower()

            # Remove filler words
            for pattern in self.spanish_fillers:
                cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)

            # Capitalize first letter
            cleaned = cleaned.strip()
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]

            # Add period if missing
            if cleaned and not cleaned[-1] in '.!?':
                cleaned += '.'

            logger.info(f"Simple cleanup: '{text}' -> '{cleaned}'")
            return cleaned

        except Exception as e:
            logger.error(f"Simple cleanup failed: {e}")
            return text

    def enhance_translation(self, spanish: str, english: str) -> str:
        """Basic translation enhancement"""
        try:
            enhanced = english

            # Apply fixes
            for pattern, replacement in self.translation_fixes.items():
                if callable(replacement):
                    enhanced = re.sub(pattern, replacement, enhanced)
                else:
                    enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)

            # Ensure proper sentence structure
            enhanced = enhanced.strip()

            # Capitalize first letter
            if enhanced:
                enhanced = enhanced[0].upper() + enhanced[1:]

            # Add period if missing
            if enhanced and not enhanced[-1] in '.!?':
                enhanced += '.'

            logger.info(f"Simple enhancement: '{english}' -> '{enhanced}'")
            return enhanced

        except Exception as e:
            logger.error(f"Simple enhancement failed: {e}")
            return english


# Singleton
_simple_processor = None

def get_simple_processor() -> SimpleTextProcessor:
    """Get simple text processor"""
    global _simple_processor
    if _simple_processor is None:
        _simple_processor = SimpleTextProcessor()
    return _simple_processor