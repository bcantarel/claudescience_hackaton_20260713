#!/usr/bin/env python3
"""
pkl_to_tsv.py — export a genes x samples expression pickle to TSV.

Bridges the Python and R WGCNA routes: scripts/01_normalize_matrix.py writes
`wgcna_input.pkl` (a pandas DataFrame, genes x samples, log2 CPM). The
canonical R driver (container/R/01_wgcna_modules.R) reads a plain TSV. This
converter makes the two routes interchangeable on the same input matrix.

Run in the `coexpr` env:
    docker compose run --rm gn py tools/pkl_to_tsv.py \
        wgcna_input.pkl results/wgcna_input.tsv

Output: TSV with a leading `gene` column (the DataFrame index) followed by one
column per sample. Gzip is chosen automatically when the path ends in `.gz`
(data.table::fread reads gz transparently).
"""
import sys
import pandas as pd


def main(argv):
    if len(argv) != 3:
        sys.exit("usage: pkl_to_tsv.py <input.pkl> <output.tsv[.gz]>")
    src, dst = argv[1], argv[2]

    df = pd.read_pickle(src)
    if not isinstance(df, pd.DataFrame):
        sys.exit(f"expected a DataFrame in {src}, got {type(df).__name__}")

    df = df.copy()
    df.index.name = "gene"
    df.to_csv(dst, sep="\t", index=True)
    print(f"wrote {dst}: {df.shape[0]} genes x {df.shape[1]} samples")


if __name__ == "__main__":
    main(sys.argv)
