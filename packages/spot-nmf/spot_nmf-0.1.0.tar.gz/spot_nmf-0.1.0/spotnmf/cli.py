"""
spotnmf Experiment Runner

This script provides an interface for running spatial transcriptomics experiments 
using the spotnmf package. It supports topic modeling-based deconvolution, 
gene set enrichment, and annotation.

Functionality:
    - run_experiment: Main function for processing spatial data and saving outputs.
    - plot: Visualize inferred topics on spatial tissue maps.
    - network: Plot networks of gene programs.
    - annotate_programs: Perform enrichment and annotation of gene programs.
    - main: Command-line interface to execute various modes (deconvolution, plotting, annotation).
"""


import argparse
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'
import time
from datetime import datetime
import pandas as pd
pd.options.display.float_format = '{:f}'.format
from typing import Union

from spotnmf.models import run_spotnmf
from spotnmf.gscore import calculate_marker_genes_topics_df
from spotnmf import io, pl, annotate, enrichment, hvg, niche_networks


def plot_programs(results_dir, sample_name, adata_spatial, is_visium=True, genome=None, is_xenograft=False, is_aggr = True):
    """
    Plot topic usages spatially for a given sample.
    """
    print("Plotting spatial topics")
    results_path = os.path.join(results_dir, sample_name)
    rf_usages = pd.read_csv(os.path.join(results_path, f"topics_per_spot_{sample_name}.csv"), index_col=0)

    if is_visium:
        if is_xenograft:
            ratio_map = {
                "GRCh38": 1 - adata_spatial.obs["admix"],
                "mm10": adata_spatial.obs["admix"]
            }
            admix_ratios = ratio_map.get(genome)
            if admix_ratios is not None:
                rf_usages = rf_usages.mul(admix_ratios, axis=0)

        if is_aggr:
            pl.plot_spatial_all_topics_aggr(
                adata_spatial,
                rf_usages=rf_usages,
                results_dir_path=results_path,
                title_name=sample_name,
                same_legend=False,
                plot_topic=True,
                filter_th = 0.9
            )
        else:
            pl.plot_spatial_all_topics_aggr_manuscript(
                adata_spatial,
                rf_usages=rf_usages,
                results_dir_path=results_path,
                title_name=sample_name,
                same_legend=False,
                COLS=5, ROWS=10,
                filter_th = 0.9
            )
            
    else:
        pl.plot_spatial_all_topics(
            adata_spatial,
            rf_usages=rf_usages,
            results_dir_path=results_path,
            title_name=sample_name,
            is_show=False,
        )


def annotate_programs(results_dir, sample_name, genome):
    """
    Run gene set enrichment and annotate topics for a given sample.
    """
    print("Annotating programs with pathway enrichment")
    results_path = os.path.join(results_dir, sample_name)
    gene_scores_df = pd.read_csv(os.path.join(results_path, f"genescores_per_topic_{sample_name}.csv"), index_col=0)

    for gene_set in ["GO:CC", "GO:BP", "KEGG", "REAC"]:
        print(f"Running enrichment for {gene_set}")
        enrichment.run_topics_pathway_enrichment(
            gene_scores_df,
            gene_set=gene_set,
            results_dir_path=results_path,
            top_n_features=1000,
            genome=genome,
            experiment_title=sample_name,
        )

    print("Matching gene sets for annotation")
    for gene_set in annotate.list_genesets(genome=genome):
        annotate.compute_genesets_annotation(
            gene_scores_df,
            gene_set,
            results_dir_path=results_path,
            max_top_genes=100,
            ranking_method="rboext",
            experiment_title=f"{sample_name}_{gene_set}",
        )


def plot_networks(results_dir: str, sample_name: str, usage_threshold: Union[float, int], n_bins: int, edge_threshold: float, annot_file: Union[str, None]):
    """
    Plot niche networks for a given sample.
    """
    print("Plotting niche networks.")

    niche_networks.plot_network_analysis(
        results_dir=results_dir,
        sample_name=sample_name,
        usage_threshold=usage_threshold,
        n_bins=n_bins,
        edge_threshold=edge_threshold,
        annot_file=annot_file
    )


def run_experiment(
    adata_spatial,
    k: int,
    sample_name: str,
    results_dir: str,
    genome=None,
    filter_genes=True,
    hvg_file=None,
    annotate=False,
    plot=False,
    network=False,
    is_visium=True,
    is_aggr = False,
    is_xenograft=False,
    usage_threshold: Union[float, int] = 0,
    n_bins: int = 1000,
    edge_threshold: float = 0.199,
    annot_file: Union[str, None] = None,
    model_params={},
    **kwargs,
):
    """
    Run a complete spotnmf experiment including model training, gene ranking, plotting, and annotation.
    """
    start_time = time.time()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Running experiment for '{sample_name}' with k = {k}")

    results_path = io.check_dir(os.path.join(results_dir, sample_name))

    # Filter genes
    if filter_genes:
        if hvg_file:
            print(f"Loading overdispersed genes from '{hvg_file}'")
            overdispersed_genes = hvg.load_hvg_list(hvg_file)

        else:
            if is_aggr:
                print(f"Computing overdispersed genes using batch mode")
                overdispersed_genes = hvg.compute_overdispersed_genes_batches(
                    adata_spatial,
                    batch_keys=["sample_id"],
                    union_agg=False,
                    **kwargs
                )
            else:
                print("Computing overdispersed genes (global mode)")
                adata_spatial, overdispersed_genes = hvg.compute_overdispersed_genes(
                    adata_spatial,
                    save_dir=results_path,
                    is_show=False,
                    n_top_genes=None,
                    **kwargs
                )
                # Save gene stats for inspection
                adata_spatial.var.to_csv(os.path.join(results_path, f"gene_stats_{sample_name}.csv"))
                
  

            # Save final list of selected genes
            hvg.save_hvg_list(overdispersed_genes, os.path.join(results_path, f"top_genes_{sample_name}.csv"))

        adata_spatial.var['highly_variable'] = adata_spatial.var.index.isin(overdispersed_genes)

    # Run topic model
    results, losses = run_spotnmf(adata_spatial, components=k, **model_params)

    # Save matrices
    for key, df in results.items():
        df.to_csv(os.path.join(results_path, f"{key}_{sample_name}.csv"))

    # Calculate and save gene scores
    print("Calculating and saving gene scores")
    gene_scores_df = calculate_marker_genes_topics_df(adata_spatial, results["topics_per_spot"])
    gene_scores_df.to_csv(os.path.join(results_path, f"genescores_per_topic_{sample_name}.csv"))

    io.save_ranked_genes(gene_scores_df, os.path.join(results_path, f"ranked_genescores_{sample_name}.csv"))
    if "genes_per_topic" in results:
        io.save_ranked_genes(results["genes_per_topic"], os.path.join(results_path, f"ranked_genes_{sample_name}.csv"))

    # Annotate topics
    if annotate:
        if not genome:
            genome = adata_spatial.uns.params["genome"]
        annotate_programs(results_dir, sample_name, genome)

    # Plot spatial maps
    if plot:
        plot_programs(results_dir, sample_name, adata_spatial, is_visium=is_visium, genome=genome, is_xenograft=is_xenograft, is_aggr = is_aggr)

    # Plot networks
    if network:
        plot_networks(results_dir, sample_name, usage_threshold=usage_threshold, n_bins=n_bins, edge_threshold=edge_threshold, annot_file=annot_file)

    # Save timing
    duration = time.time() - start_time
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Completed in {duration:.2f} seconds.")
    with open(os.path.join(results_path, f"time_{sample_name}.txt"), "w") as f:
        f.write(f"{duration}\t{losses[-1]}\t")

    return results


def main():
    """
    Command-line interface for running spotnmf experiments.
    """
    parser = argparse.ArgumentParser(description="Run spatial transcriptomics experiments with spotnmf.")
    parser.add_argument("run_type", choices=["spotnmf", "deconvolve", "plot", "annotate", "network"], help="Type of operation to perform.")
    parser.add_argument("--sample_name", required=True, help="Sample identifier.")
    parser.add_argument("--results_dir", required=True, help="Directory for saving results.")

    parser.add_argument("--adata_path", help="Path to AnnData file.")
    parser.add_argument("--k", type=int, help="Number of topics/components.")
    parser.add_argument("--genome", default="mm10", help="Reference genome (e.g., GRCh38, mm10).")
    parser.add_argument("--data_mode", default="visium", help="Data mode (e.g., visium, visium_hd).")
    parser.add_argument("--bin_size", default=16, help="Bin Size (e.g., 2, 8, 16, 24).")
    parser.add_argument("--is_xeno", action="store_true", help="Whether the dataset is a xenograft model.")
    parser.add_argument("--is_aggr", action="store_true", help="Whether data is aggregated across libraries.")
    parser.add_argument("--select_sample", default=None, help="Subset a specific sample.")
    parser.add_argument("--hvg_file", default=None, help="Precomputed highly variable genes file.")
    parser.add_argument("--usage_threshold", type=float, default=0, help="Usage threshold.")
    parser.add_argument("--n_bins", type=int, default=1000, help="Number of bins.")
    parser.add_argument("--edge_threshold", type=float, default=0.199, help="Edge threshold.")
    parser.add_argument("--annot_file", default=None, help="Annotation file.")

    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate.")
    parser.add_argument("--h", type=float, default=0.01, help="H Regularizer parameter.")
    parser.add_argument("--w", type=float, default=0.01, help="W Regularizer parameter.")
    parser.add_argument("--eps", type=float, default=0.05, help="Entropy.")
    parser.add_argument("--normalize_rows", action="store_true", help="Normalize rows of input matrix.")

    args = parser.parse_args()

    # Validate required arguments
    if args.run_type in {"spotnmf", "deconvolve"} and not (args.adata_path and args.k):
        parser.error("--adata_path and --k are required for 'spotnmf' or 'deconvolve'.")
    if args.run_type == "annotate" and not args.genome:
        parser.error("--genome is required for 'annotate'.")
    if args.run_type == "plot" and not args.adata_path:
        parser.error("--adata_path is required for 'plot'.")
    if args.run_type == "network" and (args.usage_threshold is None or args.n_bins is None or args.edge_threshold is None):
        parser.error("--usage_threshold, --n_bins, and --edge_threshold are required for 'network'.")

    is_visium = args.data_mode in {"visium", "visium_hd"}

    adata_spatial = io.read_adata(
        data_path=args.adata_path,
        data_mode=args.data_mode,
        genome=args.genome,
        is_aggr=args.is_aggr,
        is_xenograft=args.is_xeno,
        select_sample=args.select_sample,
        bin_size=args.bin_size
    )

    model_params = {
        "lr": args.lr,
        "h": args.h,
        "w": args.w,
        "eps": args.eps,
        "normalize_rows": args.normalize_rows,
    }

    if args.run_type == "spotnmf":
        run_experiment(
            adata_spatial, args.k, args.sample_name, args.results_dir,
            genome=args.genome, hvg_file=args.hvg_file,
            annotate=True, plot=True, network=True,
            is_visium=is_visium, is_xenograft=args.is_xeno, is_aggr=args.is_aggr,
            model_params=model_params
        )
    elif args.run_type == "deconvolve":
        run_experiment(
            adata_spatial, args.k, args.sample_name, args.results_dir,
            genome=args.genome, hvg_file=args.hvg_file,
            annotate=False, plot=False, network=False,
            is_visium=is_visium, is_xenograft=args.is_xeno, is_aggr=args.is_aggr,
            model_params=model_params
        )
    elif args.run_type == "plot":
        plot_programs(args.results_dir, args.sample_name, adata_spatial, is_visium=is_visium, genome=args.genome, is_xenograft=args.is_xeno, is_aggr=args.is_aggr)
    elif args.run_type == "annotate":
        annotate_programs(args.results_dir, args.sample_name, genome=args.genome)
    elif args.run_type == "network":
        plot_networks(args.results_dir, args.sample_name, args.usage_threshold, args.n_bins, args.edge_threshold, annot_file=args.annot_file)


if __name__ == "__main__":
    main()
