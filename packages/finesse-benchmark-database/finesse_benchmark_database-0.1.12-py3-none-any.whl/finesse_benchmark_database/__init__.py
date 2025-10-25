"""finesse-benchmark-database: Multilingual Atomic Probe Generator for Long-Context Evaluation

This package provides a flexible, configurable library for generating high-quality, traceable datasets of 'strings of beads'—
atomic 64-token text chunks sourced from multilingual Wikipedia articles. It serves as the foundational data generation
pipeline for the Finesse long-context benchmarking framework, ensuring reproducibility, semantic diversity, and
complete metadata tracking for advanced LLM evaluation.

Core Principles:
- Atomic Beads: Exact 64-token chunks (discard incompletes) to test pure memory granularity.
- Traceable Origins: Each bead/string includes full metadata (dataset, article_id, lang) for debugging and verification.
- Multilingual Balance: Supports 10+ languages with configurable quotas for fair coverage.
- Library-First Design: Instantiable via ProbeConfig for custom experiments; no globals or hardcoding.
- JSONL Output: Efficient streaming format for large-scale datasets.

Key Components:
- ProbeConfig: Dataclass for all settings (languages, samples, chunk size, etc.).
- generate_all_strings_of_beads(config): Produces list of {'source': metadata, 'beads': [text_chunks]} dicts.
- write_strings_to_probes_atomic(config, strings): Serializes to JSONL with auto-assigned string_ids.

Example Usage:
    from finesse_benchmark_database import ProbeConfig, generate_all_strings_of_beads, write_strings_to_probes_atomic
    
    config = ProbeConfig(
        languages=['en', 'ko'],
        samples_per_language=100,
        chunk_token_size=64,
        output_file='my_probes.jsonl',
        seed=42
    )
    
    beads_strings = generate_all_strings_of_beads(config)
    write_strings_to_probes_atomic(config, beads_strings)
    # Outputs my_probes.jsonl with ~200 traceable strings of beads.

Installation:
pip install finesse-benchmark-database
# Or via Poetry: poetry add finesse-benchmark-database

This package powers the creation of ~1M+ atomic probes for rigorous long-context memory testing.
See main.py for a full pipeline example.
"""

__version__ = "0.1.0"

from .config import ProbeConfig
from .chunker import generate_all_strings_of_beads
from .writer import write_strings_to_probes_atomic
from .main import generate_dataset