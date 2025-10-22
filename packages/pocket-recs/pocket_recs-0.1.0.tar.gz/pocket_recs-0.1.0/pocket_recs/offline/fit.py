"""Offline training pipeline orchestration."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import numpy as np
import polars as pl
from rich.console import Console
from rich.progress import Progress

from pocket_recs.config import RecommenderConfig
from pocket_recs.offline.brand_pop import build_brand_pop
from pocket_recs.offline.covis import build_covis
from pocket_recs.offline.embed import build_item_embeddings
from pocket_recs.offline.index_ann import build_ann_index, save_ann_index
from pocket_recs.offline.manifest import Manifest, compute_file_checksum, write_manifest
from pocket_recs.offline.sessionize import sessionize

console = Console()


def fit(
    interactions_path: str,
    catalog_path: str,
    out_dir: str,
    config: Optional[RecommenderConfig] = None,
    model_name: Optional[str] = None,
) -> str:
    """
    Run offline training pipeline to generate artifacts.

    Args:
        interactions_path: Path to interactions Parquet file
        catalog_path: Path to catalog CSV file
        out_dir: Output directory for artifacts
        config: Recommender configuration (optional)
        model_name: Embedding model name override (optional)

    Returns:
        Path to artifact directory
    """
    if config is None:
        config = RecommenderConfig()

    if model_name:
        config.embedding.model_name = model_name

    os.makedirs(out_dir, exist_ok=True)

    console.print("[bold blue]Starting offline training pipeline...[/bold blue]")

    with Progress() as progress:
        task = progress.add_task("[cyan]Loading data...", total=100)

        catalog = pl.read_csv(catalog_path)
        interactions = pl.read_parquet(interactions_path)
        progress.update(task, advance=20)
        console.print(f"Loaded {len(catalog)} items and {len(interactions)} interactions")

        progress.update(task, description="[cyan]Sessionizing interactions...")
        interactions = sessionize(interactions, config.covis.session_gap_minutes)
        progress.update(task, advance=10)
        console.print(f"Created {interactions['session_id'].n_unique()} sessions")

        progress.update(task, description="[cyan]Building co-visitation matrix...")
        covis = build_covis(interactions, k=config.covis.top_k, tau_ms=config.covis.tau_ms)
        progress.update(task, advance=15)
        console.print(f"Built co-visitation for {len(covis)} items")

        progress.update(task, description="[cyan]Building brand popularity...")
        interactions_with_catalog = interactions.join(
            catalog.select(["item_id", "category"]),
            on="item_id",
            how="left"
        )
        brand_pop = build_brand_pop(
            interactions_with_catalog,
            half_life_days=config.brand_pop.half_life_days,
            topn=config.brand_pop.top_n,
        )
        progress.update(task, advance=15)
        console.print(f"Built brand popularity for {len(brand_pop)} entries")

        progress.update(task, description="[cyan]Generating text embeddings...")
        texts = (
            catalog["title"].fill_null("")
            + " [SEP] "
            + catalog["brand"].fill_null("")
            + " [SEP] "
            + catalog["category"].fill_null("")
            + " [SEP] "
            + catalog["short_desc"].fill_null("")
        ).to_list()
        embeddings = build_item_embeddings(
            texts,
            model_name=config.embedding.model_name,
            batch_size=config.embedding.batch_size,
            normalize=config.embedding.normalize,
            device=config.embedding.device,
        )
        progress.update(task, advance=20)
        console.print(f"Generated embeddings: {embeddings.shape}")

        progress.update(task, description="[cyan]Building ANN index...")
        ann_index = build_ann_index(
            embeddings,
            ef_construction=config.ann.ef_construction,
            M=config.ann.M,
        )
        backend_name = ann_index[0]
        progress.update(task, advance=10)
        console.print(f"Built ANN index using {backend_name}")

        progress.update(task, description="[cyan]Persisting artifacts...")
        np.save(os.path.join(out_dir, "embeddings.npy"), embeddings)

        covis_ids = {k: v[0] for k, v in covis.items()}
        covis_weights = {k: v[1] for k, v in covis.items()}
        np.savez_compressed(
            os.path.join(out_dir, "covis.npz"), ids=covis_ids, weights=covis_weights
        )

        brand_pop.write_parquet(os.path.join(out_dir, "brand_pop.parquet"))

        ann_index_path = os.path.join(out_dir, "ann_index.bin")
        save_ann_index(ann_index, ann_index_path)

        catalog_checksum = compute_file_checksum(catalog_path)

        manifest = Manifest(
            version="0.1.0",
            model_path="lgbm.txt",
            emb_path="embeddings.npy",
            ann_path="ann_index.bin",
            ann_backend=backend_name,
            embedding_dim=int(embeddings.shape[1]),
            covis_path="covis.npz",
            brandpop_path="brand_pop.parquet",
            catalog_checksum=catalog_checksum,
            created_at=datetime.now().isoformat(),
        )
        write_manifest(out_dir, manifest)

        progress.update(task, advance=10, description="[green]Complete!")

    console.print(f"[bold green]Artifacts written to:[/bold green] {out_dir}")
    return out_dir

