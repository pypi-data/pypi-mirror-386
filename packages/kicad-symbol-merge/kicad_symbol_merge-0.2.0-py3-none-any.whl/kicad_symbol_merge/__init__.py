"""
kicad-symbol-merge
------------------
A Python utility to merge all `.kicad_sym` symbol files in a folder into one
KiCad-compatible library file (KiCad v6+).

Usage:
    kicad-symbol-merge <source_folder> <output_file>

Example:
    kicad-symbol-merge individual_symbols merged_symbols.kicad_sym
"""

from .merge import main, merge_folder, extract_symbols

__all__ = ["main", "merge_folder", "extract_symbols"]
__version__ = "0.1.0"
