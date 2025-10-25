# -*- coding: utf-8 -*-

"""single sample GSEA scoring."""

from typing import Optional

import pandas as pd
from gseapy import ssgsea


def do_ssgsea(
        filtered_expression_data: pd.DataFrame,
        gene_set: str,
        output_dir: Optional[str] = None,
        processes: int = 96,
        max_size: int = 3000,
        min_size: int = 15,
) -> pd.DataFrame:
    """Run single sample GSEA (ssGSEA) on filtered gene expression data set.

    :param filtered_expression_data: filtered gene expression values for samples
    :param gene_set: .gmt file containing gene sets
    :param output_dir: output directory
    :param processes: Number of processes
    :param max_size: Maximum allowed number of genes from gene set also the data set
    :param min_size: Minimum allowed number of genes from gene set also the data set
    :return: ssGSEA results in respective directory
    """
    single_sample_gsea = ssgsea(
        data=filtered_expression_data,
        gene_sets=gene_set,
        outdir=output_dir,  # do not write output to disk
        max_size=max_size,
        min_size=min_size,
        sample_norm_method='rank',  # choose 'custom' for your own rank list
        permutation_num=0,  # skip permutation procedure, because you don't need it
        no_plot=True,  # skip plotting to speed up
        processes=processes,
        format='png',
    )

    single_sample_gsea_df = single_sample_gsea.res2d

    if single_sample_gsea_df is None:
        raise ValueError("No results found for ssGSEA")

    single_sample_gsea_df = single_sample_gsea_df.pivot(index='Name', columns='Term', values='NES')
    single_sample_gsea_df.columns.name = None
    single_sample_gsea_df.index.name = None

    return single_sample_gsea_df
