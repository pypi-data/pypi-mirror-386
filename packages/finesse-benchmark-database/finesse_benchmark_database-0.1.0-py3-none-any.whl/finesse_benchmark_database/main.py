"""Main orchestration module for Finesse Benchmark Database Generator

This script serves as the 'Conductor' that orchestrates the entire pipeline: from configuration setup
through atomic bead generation to final JSONL serialization. It ties together config, chunker, and writer
for end-to-end execution of our 'Gemstone Necklace' production process.

Key Principles:
- Ensures all modules use the shared CONFIG for consistency.
- Executes chunking first (memory-intensive), then writing (I/O-focused).
- Comprehensive logging for audit trail and debugging.
- Designed for one-shot full generation; scale via external orchestration if needed.

Usage:
python main.py
# Runs the full pipeline: generates ~100,000 strings of beads and writes to probes_atomic.jsonl
"""

import logging

from .config import ProbeConfig
from .chunker import generate_all_strings_of_beads
from .writer import write_strings_to_probes_atomic

# Configure logging for the entire pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main() -> None:
    """Execute the full Finesse benchmark database generation pipeline as a library example.
    
    This demonstrates how users would create a ProbeConfig, generate data, and write output.
    For production, adjust config parameters as needed (e.g., more languages, larger samples).
    """
    logger.info("=== Finesse Benchmark Database Pipeline Started (Library Example) ===")
    
    # Step 1: User creates and configures ProbeConfig for this run
    logger.info("Creating test configuration...")
    test_config = ProbeConfig(
        languages=['en'],  # Single language for quick demo
        samples_per_language=5,  # Small sample for testing
        chunk_token_size=64,
        tokenizer_name="google-bert/bert-base-multilingual-cased",
        output_file="test_probes_atomic.jsonl",
        seed=42
    )
    logger.info(f"Config set: {len(test_config.languages)} languages, {test_config.chunk_token_size}-token beads, "
                f"{test_config.samples_per_language} strings per language")
    
    # Step 2: Generate all structured 'strings of beads' using the chunker
    logger.info("Starting bead generation with chunker...")
    all_strings_of_beads = generate_all_strings_of_beads(test_config)
    total_strings = len(all_strings_of_beads)
    logger.info(f"Bead generation complete: {total_strings} total strings produced "
                f"(~{total_strings / len(test_config.languages):.0f} per language)")
    
    # Step 3: Serialize to the atomic probes JSONL file using the writer
    logger.info(f"Starting serialization to {test_config.output_file}...")
    write_strings_to_probes_atomic(test_config, all_strings_of_beads)
    logger.info(f"Serialization complete: All {total_strings} strings saved with metadata.")
    
    # Final summary
    estimated_beads = sum(len(s['beads']) for s in all_strings_of_beads)
    logger.info("=== Pipeline Summary (Test Run) ===")
    logger.info(f"- Total strings: {total_strings}")
    logger.info(f"- Total atomic beads: {estimated_beads}")
    logger.info(f"- Coverage: {len(set(s['source']['lang'] for s in all_strings_of_beads))} languages")
    logger.info(f"- Output file: {test_config.output_file}")
    logger.info("For full production: Increase samples_per_language and add more languages in config.")
    logger.info("=== Finesse Benchmark Database Generation Example Finished Successfully ===")

if __name__ == "__main__":
    main()