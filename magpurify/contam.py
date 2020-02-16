#!/usr/bin/env python

import argparse
import os
import sys
from . import utility


def fetch_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=argparse.SUPPRESS,
        description="MAGpurify: known-contam module: find contigs that match a database of known contaminants",
    )
    parser.add_argument("program", help=argparse.SUPPRESS)
    parser.add_argument("fna", type=str, help="""Path to input genome in FASTA format""")
    parser.add_argument(
        "out",
        type=str,
        help="""Output directory to store results and intermediate files""",
    )
    parser.add_argument(
        "-t",
        dest="threads",
        type=int,
        default=1,
        help="""Number of CPUs to use (default=1)""",
    )
    parser.add_argument(
        "-d",
        dest="db",
        type=str,
        help="""Path to reference database
By default, the IMAGEN_DB environmental variable is used""",
    )
    parser.add_argument(
        "--pid",
        type=float,
        default=98,
        help="""Minimum %% identity to reference (default=98)""",
    )
    parser.add_argument(
        "--evalue", type=float, default=1e-5, help="""Maximum evalue (default=1e-5)"""
    )
    parser.add_argument(
        "--qcov",
        type=float,
        default=25,
        help="""Minimum percent query coverage (default=25)""",
    )
    args = vars(parser.parse_args())
    return args


def run_blastn(query, db, out, threads, qcov=25, pid=98, evalue=1e-5):
    cmd = "blastn "
    cmd += f"-query {query} "
    cmd += f"-db {db} "
    cmd += f"-out {out} "
    cmd += "-outfmt '6 std qlen slen' "
    cmd += "-max_target_seqs 1 "
    cmd += "-max_hsps 1 "
    cmd += f"-qcov_hsp_perc {qcov} "
    cmd += f"-perc_identity {pid} "
    cmd += f"-evalue {evalue} "
    cmd += f"-num_threads {threads} "
    utility.run_process(cmd)


def main():
    args = fetch_args()
    utility.add_tmp_dir(args)
    utility.check_input(args)
    utility.check_dependencies(["blastn"])
    utility.check_database(args)
    utility.add_tmp_dir(args)
    print("\n## Searching database with BLASTN")
    for target in ["hg38", "phix"]:
        db = f"{args['db']}/known-contam/{target}/{target}"
        out = f"{args['tmp_dir']}/{target}.m8"
        run_blastn(
            args["fna"],
            db,
            out,
            args["threads"],
            args["qcov"],
            args["pid"],
            args["evalue"],
        )
    print("\n## Identifying contigs with hits to db")
    flagged = set([])
    for target in ["hg38", "phix"]:
        out = f"{args['tmp_dir']}/{target}.m8"
        for r in utility.parse_blast(out):
            flagged.add(r["qname"])
    flagged = list(flagged)
    out = f"{args['tmp_dir']}/flagged_contigs"
    print(f"   {len(flagged)} flagged contigs: {out}")
    with open(out, "w") as f:
        for contig in flagged:
            f.write(contig + "\n")
