# MAGpurify

**This is not a production-ready software repository and is still under active development. Bugs and feature requests will not addressed. Please use with caution. If this code is useful, please cite: http://dx.doi.org/10.1038/s41586-019-1058-x**

This package uses a combination of different features and algorithms to identify contamination in metagenome-assembled genomes (MAGs). Contamination is defined as contigs that originated from a different species relative to the dominant organism present in the MAG.

Each module in the software package was designed to be highly specific. This means that not all contamination (contigs from other species) will be removed, but very few contigs will be incorrectly removed. Feel free to modify the default parameters for more sensitive detection of contamination.

## Installation

Clone the repo from github:
`git clone https://github.com/snayfach/MAGpurify`

Install required python libraries:
`pip install --user pandas numpy sklearn biopython`

Install 3rd party programs:

* [BLAST (v2.7.1)](https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=Download)
* [Prodigal (v2.6.3)](https://github.com/hyattpd/Prodigal)
* [HMMER (v3.1b2)](http://hmmer.org/download.html)
* [LAST (v828)](http://last.cbrc.jp)
* [Mash (v2.0)](https://github.com/marbl/Mash/releases)
* [CoverM (v0.3.2)](https://github.com/wwood/CoverM/releases)
* Make sure these programs are located on your PATH
* Tested versions indicated, but other versions might also work

Download the reference database: [MAGpurify-db-v1.0.tar.bz2](http://bit.ly/MAGpurify-db)

And unpack the database:
`tar -jxvf MAGpurify-db-v1.0.tar.bz2`

Update your environment:
`export PATH=$PATH:/path/to/MAGpurify`
`export MAGPURIFYDB=/path/to/MAGpurify-db-v1.0`


## A quick overview

The program is broken down into several modules:

```
$ run_qc.py -h

MAGpurify: Identify and remove incorrectly binned contigs from metagenome-assembled genomes

Usage: run_qc.py <command> [options]

Commands:
    phylo-markers: find taxonomic discordant contigs using db of phylogenetic marker genes
    clade-markers: find taxonomic discordant contigs using db of clade-specific marker genes
      conspecific: find contigs that fail to align to closely related genomes
       tetra-freq: find contigs with outlier tetranucleotide frequency
       gc-content: find contigs with outlier gc content
         coverage: find contigs with outlier coverage profile
     known-contam: find contigs that match a database of known contaminants
        clean-bin: remove identified contigs from bin

Note: use run_qc.py <command> -h to view usage for a specific command
```

MAGpurify modules are executed sequentially using the following command structure:

```
$ run_qc.py <module> <input mag> <output directory>
```

After the desired modules have been executed, the flagged contigs are removed:

```
$ run_qc.py clean-bin <input mag> <output directory> --output-fasta <output mag>
```

It's as simple as that!

## Dependency on external data

`tetra-freq` and `gc-content` don't rely on external data. The `phylo-markers`, `clade-markers` and `known-contam` modules can be run using the standard MAGpurify database. The `conspecific` module requires that you build your own database. The `coverage` module requires input BAM files.

## An example using the default database

The next few lines will show you how to run the software using a single MAG included with the software.

First, run the individual modules to predict contamination in the example `example/test.fna` file and store the results in `example/output`:

```
$ run_qc.py phylo-markers example/test.fna example/output
$ run_qc.py clade-markers example/test.fna example/output
$ run_qc.py tetra-freq example/test.fna example/output
$ run_qc.py gc-content example/test.fna example/output
$ run_qc.py known-contam example/test.fna example/output
```

The output of each module is stored in the output directory:
```
$ ls example/output

clade-markers gc-content known-contam phylo-markers tetra-freq
```

Now remove the contamintion from the bin with `clean-bin`:

```
$ run_qc.py clean-bin example/test.fna example/output --output-fasta example/test_cleaned.fna

## Reading genome bin
   genome length: 704 contigs, 4144.3 Kbp

## Reading flagged contigs
   phylo-markers: 1 contigs, 17.18 Kbp
   clade-markers: 3 contigs, 17.1 Kbp
   conspecific: no output file found
   tetra-freq: 0 contigs, 0.0 Kbp
   gc-content: 0 contigs, 0.0 Kbp
   coverage: no output file found
   known-contam: 0 contigs, 0.0 Kbp

## Removing flagged contigs
   removed: 4 contigs, 34.28 Kbp
   remains: 700 contigs, 4110.03 Kbp
   cleaned bin: example/test_cleaned.fna
```

In summary, 2 of the 7 modules predicted at least one contaminant and the cleaned bin was written to `example/output/cleaned_bin.fna`

## An example using the `conspecific` module

To run the `conspecific` module, you need to build your own reference database using Mash. We've provided some dummy files to illustrate this (but you shouldn't use them with your data!):

```
$ mash sketch -l example/ref_genomes.list -o example/ref_genomes
```

This command will create a Mash sketch of the genomes listed in `example/ref_genomes.list` that are located in `example/ref_genomes`. The sketch will be written to `example/ref_genomes.msh`

Now you can run the conspecific module:

```
$ run_qc.py conspecific example/test.fna example/output --mash-sketch example/ref_genomes.msh

## Finding conspecific genomes in database
   25 genomes within 0.05 mash-dist
   list of genomes: example/output/conspecific/conspecific.list
   mash output: example/output/conspecific/mash.dist

## Performing pairwise alignment of contigs in bin to database genomes
   total alignments: 12125

## Summarizing alignments
   contig features: example/output/conspecific/contig_hits.tsv

## Identifying contigs with no conspecific alignments
   238 flagged contigs, 450.02 Kbp
   flagged contigs: example/output/conspecific/flagged_contigs
```

So, the conspecific module alone identified 238 putative contaminants! This illustrates that this module can be very sensitive when your MAG is similar to closely related genomes in your reference database… or to other MAGs!

## An example using the `coverage` module

To run the `coverage` module, you need to input a sorted BAM file containing reads mapped to the MAG (or the original metagenome, as long as the contig name is unchanged). You can also input multiple BAM files and MAGpurify will pick the one with the greatest average contig coverage.

```
$ run_qc.py conspecific example/test.fna example/output --bams ./BAM/sample_1.bam ./BAM/sample_2.bam ./BAM/sample_3.bam

## Computing contig coverage

## Identifying outlier contigs

## Sample being used for outlier detection: sample_2
   2 flagged contigs: example/output/coverage/flagged_contigs
```

## Details on the individual modules

### phylo-markers
This module works by taxonomically annotating your contigs based on a database of phylogenetic marker genes from the PhyEco database and identifying taxonomically discordant contigs.

### clade-markers
This module works in a very similar way to `phylo-markers`, but instead uses clade-specific markers from the MetaPhlAn 2 database for taxonomic annotation.

### conspecific
The logic behind this module is that strains of the same species should have similarity along most of the genome. Therefore, this module works by first finding strains of the same species, and then performing pairwise alignment of contigs. Contaminants are identified which do not align at all between genomes.

### tetra-freq
This module works by identifying contigs with outlier nucleotide composition based on tetranucleotide frequencies (TNF). In order to reduce TNF down to a single dimension, principal component analysis (PCA) is performed and the first principal component is used.

### gc-content
This module works by identifying contigs with outlier nucleotide composition based on GC content.

### coverage
This module works by identifying contigs with outlier coverage based on read mapping information.

### known-contam
This module works by identifying contigs that match a database of known contaminants. So far, the human genome and phiX genome are the only ones in the database.