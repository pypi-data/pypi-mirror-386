"""Configuration module for Finesse Benchmark Database Generator

This module holds all configurable parameters for generating atomic probes from Wikimedia Wikipedia datasets.
Based on the 'Beads and String' model: 64-token atomic beads from diverse languages, ensuring semantic continuity within strings but independence across probes.

Key Principles:
- Fixed 64-token chunk size for atomic beads.
- Balanced sampling across languages for global diversity.
- Seeded randomness for perfect reproducibility.
- Output in probes_atomic.jsonl format for dynamic assembly in evaluation.

Usage:
from config import tokenizer_name, languages, chunk_token_size, samples_per_language, output_file, seed
"""

from dataclasses import dataclass
import random

@dataclass
class ProbeConfig:
    """Central configuration for probe generation.
    
    This dataclass serves as a flexible template for library users.
    Instantiate and populate it with desired values before passing to generate functions.
    
    Example:
        config = ProbeConfig(
            languages=['en', 'ko'],
            samples_per_language=10,
            chunk_token_size=64
        )
    """
    
    # Tokenizer for tokenization (default: multilingual BERT)
    tokenizer_name: str = "google-bert/bert-base-multilingual-cased"
    
    # Languages for balanced multilingual coverage (must be set by user)
    languages: list[str] = None
    
    # Atomic bead size (golden rule from design; override for custom experiments)
    chunk_token_size: int = 64

    # Number of 'strings of beads' (source documents) per language: The number of complete
    # Wikipedia articles to process per language. Each document is chunked sequentially into
    # multiple 64-token atomic beads, preserving original order and semantic flow within
    # the string. This is NOT the total count of individual beads (which will be much higher,
    # depending on document lengths), but the number of such connected 'necklaces' or
    # 'strings' for balanced multilingual coverage.
    samples_per_language: int = 10000
    
    # Output file for atomic probes
    output_file: str = "probes_atomic.jsonl"
    
    # Fixed seed for reproducibility (immutable law; set to None for non-deterministic runs)
    seed: int = 42

def get_config() -> ProbeConfig:
    """Instantiate and return the configuration with languages initialized."""
    config = ProbeConfig()
    config.languages = [
        'en',  # English
        'ko',  # Korean
        'es',  # Spanish
        'ja',  # Japanese
        'ru',  # Russian
        'zh',  # Chinese
        'ar',  # Arabic
        'id',  # Indonesian
        'de',  # German
        'vi',  # Vietnamese
    ]
    
    # Set global seed for all randomness
    random.seed(config.seed)
    
    return config

# Default config instance
CONFIG = get_config()