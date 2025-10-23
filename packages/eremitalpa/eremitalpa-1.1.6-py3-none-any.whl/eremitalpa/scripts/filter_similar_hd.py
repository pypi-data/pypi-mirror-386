from eremitalpa import filter_similar_hd
from Bio.SeqIO import parse, write
from sys import stdin, stdout
import argparse


def main():
    parser = argparse.ArgumentParser(
        "ere-filter-similar-hd",
        description="Filter sequences that have a hamming distance of less than n to any "
        "already seen. Reads from stdin, writes to stdout. Case sensitive.",
    )
    parser.add_argument(
        "--n", required=True, type=float, help="Hamming distance threshold"
    )
    parser.add_argument("--ignore", default="-X", help="Default: -X")
    parser.add_argument("--progress_bar", help="Show progress bar", action="store_true")
    parser.add_argument(
        "--case_sensitive", help="Case sensitive comparison", action="store_true"
    )
    args = parser.parse_args()

    records = parse(stdin, "fasta")
    subset = filter_similar_hd(
        records,
        n=args.n,
        progress_bar=args.progress_bar,
        ignore=set(args.ignore),
        case_sensitive=args.case_sensitive,
    )
    write(subset, stdout, "fasta")
