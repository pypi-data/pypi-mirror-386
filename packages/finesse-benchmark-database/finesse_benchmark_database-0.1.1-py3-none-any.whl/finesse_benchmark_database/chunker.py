"""Chunker module for Finesse Benchmark Database Generator

This module implements the 'Gemstone Necklace Crafter' aka the atomic bead generator.
It transforms raw Wikimedia Wikipedia documents into 'strings of beads': sequential chains
of exactly 64-token atomic beads from each source article, preserving semantic flow within
each string while ensuring atomicity and reproducibility across languages.

Key Principles:
- Uses official reference tokenizer: bert-base-multilingual-cased for universal fairness.
- Exactly 64-token beads only; discard all incomplete final chunks (golden rule).
- One 'string' per Wikipedia article, with beads in original sequential order.
- Balanced collection: samples_per_language strings per language.
- Streaming processing for efficiency on massive datasets.
- Logged progress for transparency and debugging.

Usage:
from chunker import generate_all_strings_of_beads
strings_of_beads = generate_all_strings_of_beads()
# Result: List[Dict] where each inner dict contains 'source' and 'beads' keys.
"""

import logging
import random
from typing import List, Dict

from .config import ProbeConfig
from datasets import load_dataset
from transformers import AutoTokenizer

# Configure logging for progress tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_all_strings_of_beads(config: ProbeConfig) -> List[Dict]:
    """
    Generate all 'strings of beads' across languages using the official tokenizer.
    
    Args:
        config: ProbeConfig instance with all parameters (languages, samples_per_language, etc.).
    
    For each language:
    - Stream Wikipedia articles.
    - For each article (up to config.samples_per_language):
      - Tokenize the full text.
      - Sequentially slice into 64-token chunks.
      - Decode only exact 64-token chunks to bead texts.
      - Form a 'string' as [bead1, bead2, ...] if at least one bead exists.
    - Collect all strings into a global 2D list.
    
    Returns:
        List of dictionaries: Outer list by language/order, inner dicts contain 'source' and 'beads' keys.
    """
    # Set global seed for reproducibility
    random.seed(config.seed)
    
    # Load the official reference tokenizer (our 'public scale')
    logger.info(f"Loading official tokenizer: {config.tokenizer_name}")
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_name)
    
    all_strings_of_beads: List[Dict] = []
    
    if config.languages is None:
        raise ValueError("config.languages must be set to a list of language codes.")
    
    for lang in config.languages:
        logger.info(f"Starting processing for language: {lang} (target: {config.samples_per_language} strings)")
        
        # Load streaming dataset with the specified split
        dataset = load_dataset(
            "wikimedia/wikipedia",
            f"20231101.{lang}",
            streaming=True,
            split="train"
        )
        
        strings_for_lang: List[Dict] = []
        article_count = 0
        
        for example in dataset:
            if len(strings_for_lang) >= config.samples_per_language:
                break
            
            # Extract and clean text
            text = example.get("text", "").strip()
            if not text:
                continue
            
            # Extract article ID for metadata
            article_id = example.get("id", "")
            
            # Tokenize the full article
            tokens = tokenizer.encode(text, add_special_tokens=False)
            
            # Sequentially chunk into exact config.chunk_token_size-token beads
            beads: List[str] = []
            for i in range(0, len(tokens), config.chunk_token_size):
                chunk_tokens = tokens[i:i + config.chunk_token_size]
                
                # Golden rule: Only accept exactly 64 tokens; discard incompletes
                if len(chunk_tokens) == config.chunk_token_size:
                    bead_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True).strip()
                    if bead_text:  # Ensure non-empty after decoding
                        beads.append(bead_text)
            
            # Only add the string if it has at least one bead
            if beads:
                string_data = {
                    "source": {
                        "dataset": "wikimedia/wikipedia",
                        "article_id": article_id,
                        "lang": lang
                    },
                    "beads": beads
                }
                strings_for_lang.append(string_data)
                article_count += 1
                
                # Log progress every 100 articles
                if article_count % 100 == 0:
                    logger.info(
                        f"Language {lang}: Processed {article_count} articles, "
                        f"collected {len(strings_for_lang)} strings so far"
                    )
        
        # Add language's strings to the global collection
        all_strings_of_beads.extend(strings_for_lang)
        logger.info(f"Completed {lang}: {len(strings_for_lang)} strings generated "
                    f"(from {article_count} articles)")
    
    total_strings = len(all_strings_of_beads)
    logger.info(f"Generation complete: {total_strings} total strings of beads across {len(config.languages)} languages")
    
    return all_strings_of_beads

if __name__ == "__main__":
    # Example library usage: Create config and generate
    from config import ProbeConfig
    
    # User creates and populates config
    test_config = ProbeConfig(
        languages=['en', 'ko'],  # Test with 2 languages
        samples_per_language=5,  # Small sample for demo
        chunk_token_size=64,
        tokenizer_name="google-bert/bert-base-multilingual-cased",
        output_file="probes_atomic.jsonl",
        seed=42
    )
    
    # Generate and print summary
    strings = generate_all_strings_of_beads(test_config)
    print(f"Generated {len(strings)} strings of beads.")
    if strings:
        avg_beads_per_string = sum(len(s['beads']) for s in strings) / len(strings)
        print(f"Average beads per string: {avg_beads_per_string:.2f}")