"""
Polyase: A package for analyzing allele-specific expression in polyploid plants.

This package provides tools for calculating and analyzing allelic ratios,
visualizing allele-specific expression patterns, and statistical testing
of allelic imbalance in polyploid plant genomes.
"""

__version__ = "0.1.8"
__author__ = "Nadja Nolte"

from .allele_utils import AlleleRatioCalculator, calculate_allelic_ratios
from .multimapping import MultimappingRatioCalculator, calculate_multi_ratios, calculate_per_allele_ratios
from .filter import filter_low_expressed_genes
from .plotting import plot_allelic_ratios, plot_top_differential_syntelogs, plot_top_differential_isoforms, plot_isoform_diu_results, plot_differential_isoform_usage, plot_allele_specific_isoform_structure
from .ase_data_loader import load_ase_data, aggregate_transcripts_to_genes
from .stats import test_allelic_ratios_between_conditions, test_allelic_ratios_within_conditions, get_top_differential_syntelogs, test_isoform_DIU_between_conditions, test_differential_isoform_structure
from .structure import add_exon_structure, add_structure_from_gtf

__all__ = ["filter_low_expressed_genes","AlleleRatioCalculator", "calculate_allelic_ratios", "MultimappingRatioCalculator", "calculate_multi_ratios","plot_allelic_ratios", "load_ase_data", "aggregate_transcripts_to_genes", "test_allelic_ratios_between_conditions", "test_allelic_ratios_within_conditions","plot_top_differential_syntelogs", "plot_top_differential_isoforms", "get_top_differential_syntelogs", "test_isoform_DIU_between_conditions", "calculate_per_allele_ratios", "add_exon_structure", "plot_isoform_diu_results", "add_structure_from_gtf", "test_differential_isoform_structure", "plot_differential_isoform_usage", "plot_allele_specific_isoform_structure"]
