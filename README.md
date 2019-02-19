# GraphBin: Improved Binning of Metagenomic Contigs using Assembly Graphs

**GraphBin** is a metagenomic contig binning tool that makes use of the contig connectivity information from the assembly graph to bin contigs. It utilizes the binning result of an existing binning tool and a label propagation algorithm to correct mis-binned contigs and predict the labels of contigs which are discarded due to short length.

## Dependencies
GraphBin is coded in Python 3.6. To run GraphBin, you will need to install the following python modules.
* [python-igraph](https://igraph.org/python/)
* [python-labelpropagation](https://github.com/ZwEin27/python-labelpropagation)

You can go to these links and follow the instructions to download these modules.

## Downloading GraphBin
To download GraphBin, you have to clone the GraphBin repository to your machine.

```
git clone https://github.com/Vini2/GraphBin.git
```
## Assembly
Use [**SPAdes**](http://cab.spbu.ru/software/spades/) software to assemble reads into contigs. Use the metagenomics mode for assembly.

Once you have obtained the assembly output, you can run GraphBin.

## Using GraphBin
You can see the usage options of GraphBin by typing ```python graphbin.py -h``` on the command line.

```
usage: graphbin.py [-h] --graph GRAPH --contigs CONTIGS --paths PATHS --n_bins N_BINS --binned BINNED --output OUTPUT

optional arguments:
  -h, --help         show this help message and exit
  --graph GRAPH      path to the assembly graph file
  --contigs CONTIGS  path to the contigs.fasta file
  --paths PATHS      path to the contigs.paths file
  --binned BINNED    path to the .csv file with the initial binning output
                     from an existing tool
  --output OUTPUT    path to the output folder
```
## Input Format

GraphBin takes in 4 files as inputs.
* Assembly graph file (in .gfa format)
* Nucleotide sequences of contigs(in .fasta format)
* Paths of contigs (in .paths format)
* Binning output from an existing tool (in .csv format)

**Note:** The binning output file should have comma separated values ```(node_number, bin_number)``` for each contig. For example,

```
1,1
2,1
3,2
4,2
5,1
...
```

## Example Usage

```
python graphbin.py --graph /path/to/graph_file.gfa --contigs /path/to/contigs_file.fasta --paths /path/to/paths_file.paths --binned /path/to/binning_result.csv --output /path/to/output_folder
```

## References
[1] Wu, Y.W., Tang, Y.H., Tringe, S.G., Simmons, B.A., Singer, S.W.: MaxBin: an automated binning method to recover individual genomes from metagenomes using an expectation-maximization algorithm. Microbiome 2(26), (2014)

[2] Wu, Y.W., Simmons, B.A., Singer, S.W.: MaxBin 2.0: an automated binning algorithm to recover genomes from multiple metagenomic datasets. Bioinformatics 32(4), (2016)

[3] Sczyrba, A., et. al : Critical Assessment of Metagenome Interpretation a Benchmark of Metagenomics Software. Nature Methods 14, 1063-1071 (2017)

[4] Barnum, T.P., et al.: Genome-resolved metagenomics identifies genetic mobility, metabolic interactions, and unexpected diversity in perchlorate-reducing communities. The ISME Journal 12, 1568-1581 (2018)

[5] Bankevich, A., et al.: SPAdes: A New Genome Assembly Algorithm and Its Applications to Single-Cell Sequencing. Journal of Computational Biology 19(5), 455-477 (2012)

[6] Nurk, S., Meleshko, D., Korobeynikov, A., Pevzner, P.A.: metaSPAdes: a new versatile metagenomic assembler. Genome Researcg 5, 824-834 (2017)

[7] Zhu, X., Ghahramani, Z.: Learning from Labeled and Unlabeled Data with Label Propagation. Technical Report CMU-CALD-02, Carnegie Mellon University, (2002)
