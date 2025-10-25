"""Writer module for Finesse Benchmark Database Generator

This module implements the 'Eternal Scribe': it takes the structured 'strings of beads' output from chunker.py
and serializes them into probes_atomic.jsonl format. Each line is an independent JSON object with metadata
for full traceability, ensuring the dataset is reproducible, queryable, and efficient for large-scale use.

Key Principles:
- JSONL format for streaming efficiency (one complete JSON object per line).
- Assigns immutable 'string_id' for unique identification.
- Preserves all source metadata (dataset, article_id, lang) for debugging and verification.
- UTF-8 encoding to handle multilingual content without corruption.
- Logged serialization progress for transparency.

Usage:
from writer import write_strings_to_probes_atomic
from chunker import generate_all_strings_of_beads
strings = generate_all_strings_of_beads()
write_strings_to_probes_atomic(strings)
# Results in probes_atomic.jsonl with all probes serialized.
"""

import json
import logging
from typing import List, Dict

from .config import ProbeConfig

# Configure logging for progress tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_strings_to_probes_atomic(config: ProbeConfig, all_strings_of_beads: List[Dict]) -> None:
    """
    Write the structured strings of beads to the atomic probes JSONL file.
    
    Args:
        config: ProbeConfig instance specifying output_file and SEED.
        all_strings_of_beads: List of dicts from chunker.py, each with 'source' and 'beads'.
    
    Side Effects:
        Creates/appends to config.output_file.
        Each string gets a sequential 'string_id' assigned.
    """
    output_path = config.output_file
    logger.info(f"Starting serialization to {output_path}. Total strings: {len(all_strings_of_beads)}")
    
    with open(output_path, 'w', encoding='utf-8') as file:
        for i, string_data in enumerate(all_strings_of_beads):
            # Assign unique string_id (immutable global identifier)
            string_data['string_id'] = i
            
            # Serialize to JSON line
            json_line = json.dumps(string_data, ensure_ascii=False, separators=(',', ':'))
            file.write(json_line + '\n')
            
            # Log progress every 1000 strings
            if (i + 1) % 1000 == 0:
                logger.info(f"Serialized {i + 1} strings to {output_path}")
    
    total_written = len(all_strings_of_beads)
    logger.info(f"Serialization complete: {total_written} strings written to {output_path}")
    logger.info(f"File structure: Each line is a JSON object with 'string_id', 'source' (metadata), and 'beads' ({config.chunk_token_size}-token chunks).")

if __name__ == "__main__":
    # Example library usage: Create config and run full pipeline
    from config import ProbeConfig
    from chunker import generate_all_strings_of_beads
    
    # User creates and populates config for a small test run
    demo_config = ProbeConfig(
        languages=['en'],  # Single language for quick demo
        samples_per_language=3,  # Very small sample
        chunk_token_size=64,
        tokenizer_name="google-bert/bert-base-multilingual-cased",
        output_file="demo_probes_atomic.jsonl",
        seed=42
    )
    
    print("Generating strings of beads...")
    strings = generate_all_strings_of_beads(demo_config)
    print(f"Generated {len(strings)} strings. Now serializing...")
    write_strings_to_probes_atomic(demo_config, strings)
    print("Pipeline complete. Check demo_probes_atomic.jsonl for output.")