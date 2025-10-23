# FAQ

Frequently asked questions.

## Model inputs

### How do I make predictions for a specific genomic region?

You can define any region in either the human or mouse genome, and use the API
to predict various outputs. See the [quick start colab](colabs/quick_start) for
a demonstration.

### How do I specify a genomic region?

Using the {class}`genome.Interval<alphagenome.data.genome.Interval>` class,
which is initialized with a chromosome, a start, and an end position.

<!-- mdformat off(Turn off mdformat to retain myst syntax.) -->

:::{note}
AlphaGenome classes such as {class}`genome.Interval<alphagenome.data.genome.Interval>`
uses 0-based indexing, consistent with the underlying Python implementations.

This means an
{class}`genome.Interval<alphagenome.data.genome.Interval>` includes the base
pair at the `start` position up to the base pair at the `end-1` position.

For example, to specify the first base pair of chromosome 1, use
`genome.Interval('chr1', 0, 1)`. This interval has a width of 1, and contains
only the base pair at the first position of chromosome 1.

To interpret interval overlaps, remember that 0-based indexing excludes the base
pair at the `end` position itself, such that
`genome.Interval('chr1', 0, 1).overlaps(genome.Interval('chr1', 1, 2))`
returns `False`.
:::

<!-- mdformat on -->

### What are the reference genome versions used by the model?

We use human genome assembly hg38 (GRCh38.p13.genome.fa) and mouse assembly mm10
(GRCm38.p6.genome.fa). For other genome builds (such as hg19, for example), the
[LiftOver](https://genome.ucsc.edu/cgi-bin/hgLiftOver) tool can be used to
convert from hg38 coordinates to the desired assembly.

### Can I make a prediction for any arbitrary DNA sequence?

Yes, you can make predictions for any sequence, provided it is within the range
of sequence lengths supported by the model. Note that model predictions have
only been evaluated using sequences that vary by a relatively small amount from
the reference genome (SNPs and indels), so very large differences from the human
reference genome (for example, structural variants, sequences with a large
amount of padding, synthetic sequences, or artificial DNA constructs) may result
in predictions that are not as reliable.

### Can I make predictions for DNA from other species?

Yes, with the caveat that the model has only been trained on mouse and human
DNA. Prediction quality is likely to degrade as evolutionary distance from these
two species increases, but note that this has not been formally benchmarked.

### What is the longest sequence the model can take as input?

1MB (precisely 2^20 base-pairs long). Other sequence lengths are also supported:
\~2KB, \~16KB, \~100KB, \~500KB.

### How do I request predictions for a sequence with a length that is not in the list of supported lengths?

You can use
{func}`genome.Interval.resize<alphagenome.data.genome.Interval.resize>` to crop
or expand your sequence length to the nearest supported length.

Note that `.resize` expands sequences using the actual surrounding genomic data,
not by adding padding.

## Model outputs

### How many tracks are there per output type and what do they represent?

This varies from 5 to over 600. Each of the tracks refers to a particular
cell-type or tissue, as well as other properties, such as strand or a specific
transcription factor (for the `CHIP_TF` output type). See the
[output metadata documentation](project:exploring_model_metadata.md#Exploring-model-metadata)
for a full list of the output types.

### How do I find out what tissue or cell-type an output ‘track’ refers to?

Using the [navigating data ontologies notebook](colabs/tissue_ontology_mapping),
you can look at the output metadata where biosample names and ontology CURIEs
(IDs) for each track are described.

### What is an ontology CURIE?

CURIEs (Compact Uniform Resource Identifiers) are standardized, abbreviated
codes (e.g., ‘UBERON:0001114’ for liver) that uniquely identify specific
ontology terms.

### Where are your ontology CURIEs sourced from?

We source these from the IDs provided in the source training data. We also
restricted the ontology types to UBERON, CL, CLO and EFO, following ENCODE
practices. We recommend using EBI's
[Ontology Lookup Service](https://www.ebi.ac.uk/ols4) to understand
relationships between the ontology IDs for different tracks.

### What is strandedness?

DNA is double-stranded, meaning that there are two nucleotide strands that form
the double helix. By convention, one of those molecules is designated the
forward, or positive strand (5'->3'), and the other is designated the reverse,
or negative strand (3'->5').

Genomic assays can either be unstranded or stranded (also called
strand-specific).

*   Unstranded assays return results that do not distinguish whether a
    measurement came from the positive or negative strand. Certain assays do not
    generate stranded information – for example, ATAC-seq generates unstranded
    accessibility information.
*   Stranded (or strand-specific) assays annotate each measurement as coming
    from the positive or negative strand. This is important for transcriptional
    assays to distinguish between strand-specific transcripts (for example, two
    transcripts that share a transcriptional start site but are on different
    strands).

<!-- mdformat off(Turn off mdformat to retain myst syntax.) -->

:::{note}
Not all RNA-seq samples will be stranded, especially those that are
from older experiments. For example, GTEx RNA-seq data is unstranded.
:::

<!-- mdformat on -->

For more general information about the difference between non-stranded and
stranded protocols and how to interpret them, there is a helpful tutorial
[here](https://www.ecseq.com/support/ngs/how-do-strand-specific-sequencing-protocols-work).

### How is strandedness handled in model outputs?

In the model output metadata, we use the following symbols to designate the
strand of a track:

*   positive: `+`
*   negative: `-`
*   unstranded `.`

For assays that were performed in a stranded (or strand-specific) manner, the
assay will have two tracks per cell or tissue type: one for the positive (`+`)
and another for the negative (`-`) strand.

For unstranded assays, there will be a single track per cell or tissue type,
annotated as unstranded (`.`).

We provide convenience operations for manipulating
{class}`~alphagenome.data.track_data.TrackData` based on strand information,
such as
{func}`~alphagenome.data.track_data.TrackData.filter_to_negative_strand`, etc.

### How can I save the model outputs?

For *variant effect predictions*: We recommend converting the scores into a
pandas DataFrame. This DataFrame can then be easily exported to a common file
format, such as a CSV file, for use with other tools or for record-keeping.
Specific instructions and examples for this process are provided in our 'Variant
Scoring UI' tutorial.

For *genome track predictions (e.g., RNA-seq levels)*: The predicted track data
is provided as NumPy arrays within TrackData objects. These arrays can be
directly saved to disk using standard NumPy functions, such as `numpy.save` (for
saving a single array to a `.npy` file) or `numpy.savez_compressed` (for saving
multiple arrays into a single compressed `.npz` file).

### What are some of the limitations of the model?

AlphaGenome has several key limitations:

-   *Tissue-specificity and long-range interactions*: While AlphaGenome shows
    improvements in these areas compared to previous models, accurately
    capturing tissue-specific effects and long-range genomic interactions
    remains challenging for deep learning models in genomics, requiring further
    research.
-   *Species scope*: The model is trained and evaluated on human and mouse DNA.
    Its performance on DNA from other species has not been determined.
-   *Personal genomes*: The model has not yet been benchmarked for predicting
    individual (personal) human genomes.
-   *Molecular scope*: AlphaGenome predicts the molecular consequences of
    genetic variations. Its direct applicability to complex trait analysis is
    limited, as these traits also involve broader biological processes (e.g.,
    gene function, development, environmental factors) beyond the model's
    primary focus.
-   *Unphased training and single sequence input*: The model processes a single
    DNA sequence at a time and is therefore not inherently 'diploid-aware'. It
    was trained using unphased data, meaning it could not learn to distinguish
    between alleles inherited from the mother versus the father. Consequently,
    its variant effect predictions do not inherently model heterozygous states
    (i.e., the presence of both a reference and a variant allele at a site
    simultaneously).

## Visualizing predictions

### How do I visualize the predicted output?

You can use any tool to visualize the numerical output, but we provide a Python
[visualization library](project:api/visualization.md#Visualization) so you can
easily visualize the output immediately. You can use our
[visualization basics guide](project:visualization_library_basics.md) and see
examples of how to plot different modalities in our
[visualizing predictions tutorial](colabs/visualization_modality_tour).

### Can I design my own visualizations to work with this library?

Yes. The returned figures are based on matplotlib, so should be extendible.
Additionally, you can choose to work with the raw output data and design your
own visualizations.

### Where are the plotted transcript annotations from?

Transcript annotations are sourced from standard Gene Transfer Format (GTF)
files from GENCODE: the hg38 reference assembly (release 46) for human and the
mm10 reference assembly (release M23) for mouse.

### Am I limited to only plotting protein-coding genes, and only the longest transcript?

No. If you wish to include other gene types or all transcripts (not just the
longest), you can remove the respective calls to
`gene_annotation.filter_protein_coding(gtf)` and
`gene_annotation.filter_to_longest_transcript(gtf)` in your code. Note that
including more transcripts can make the plot appear busy; you can adjust the
`fig_height` parameter of the `TranscriptAnnotation` plot component to improve
legibility.

## Variant scoring

### How do I define a variant?

By creating a {class}`~alphagenome.data.genome.Variant` object.

<!-- mdformat off(Turn off mdformat to retain myst syntax.) -->

:::{note}
:name: variant-position-is-1-based
As mentioned above, AlphaGenome classes such as
{class}`~alphagenome.data.genome.Variant` use 0-indexing, and Variant's
{func}`~alphagenome.data.genome.Variant.start` and
{func}`~alphagenome.data.genome.Variant.end` contain 0-indexed values.

However, most variants in public databases, such as dbSNP, are provided as
1-indexed.

To enable compatibility with these annotations, the
{class}`~alphagenome.data.genome.Variant` object is initialized with a
1-indexed {attr}`~alphagenome.data.genome.Variant.position` attribute, which is
then converted to 0-indexing internally. (i.e.,
{func}`~alphagenome.data.genome.Variant.start` returns
{attr}`~alphagenome.data.genome.Variant.position` - 1).

See the {class}`~alphagenome.data.genome.Variant` docstring for more details.
:::

<!-- mdformat on -->

### Are there tools to help me define variants, and run inference for them?

See the
[scoring and visualizing a single variant notebook](colabs/variant_scoring_ui)
which walks through how to define a {class}`~alphagenome.data.genome.Variant`
object and perform inference. Batch inference over many variants can be
performed using the
[batch variant scoring notebook](colabs/batch_variant_scoring) which takes a
variant call file (VCF) as input.

### Can I pass any sequence to {class}`~alphagenome.data.genome.Variant.reference_bases` or does it have to match the reference genome sequence at the variant location?

You can pass any sequence to
{class}`~alphagenome.data.genome.Variant.reference_bases`. Note that
{func}`~alphagenome.models.dna_client.DnaClient.predict_variant` is agnostic to
the alleles in the reference genome, but rather uses the REF/ALT alleles
specified by the user.

### Are variant predictions for insertions and deletions (indels) supported?

Yes. We use left-alignment to specify indels. See
{class}`~alphagenome.data.genome.Variant` for more details. For scoring indels,
we adopt SpliceAI's {cite:p}`spliceai` indel alignment strategy: inserted bases
are summarized by taking the maximum value over the inserted segment, while
deleted bases are treated as having zero signal in the `ALT` context, thereby
enabling consistent positional comparisons.

### Which variant scorer should I use for a given modality?

In practice, you can use most variant scoring strategies for any modality.
However, we provide a recommendation for the best strategies based on our
evaluations in the
[variant scoring documentation](project:variant_scoring.md#variant-scoring).

### Can I write my own variant scoring strategy?

We do not currently support users writing their own variant scoring strategy.
However, since variant scoring is simply aggregating REF and ALT track
predictions, you can write your own methods for handling these values.

### What is the difference between a 'quantile_score' and 'raw_score'?

The 'raw_score' is the output for a particular variant scoring strategy.
However, different tracks and modalities yield scores that are on different
scales. For instance, the
[Splice Sites Usage scorer](project:variant_scoring.md#splicing-splice-site-usage)
returns values between 0 and 1, whereas the
[Gene Expression (RNA-seq)](project:variant_scoring.md#gene-expression-rna-seq)
scorer returns negative or positive values without bounds. To facilitate
comparisons across tracks and different variant scoring strategies, we use an
empirical quantiles approach (see {cite:p}`alphagenome` for full details).
Briefly, we estimate a background distribution for each variant scorer and track
using scores for common variants (MAF>0.01 in any GnomAD v3 population). We can
then convert any 'raw score' into a 'quantile score', representing its rank
within this background distribution. E.g. a variant with a quantile score of
0.99 has a score equivalent to the 99th percentile of common variants. This
provides a measure of predicted impact that is standardized to the same scale
across different variant scorers and tracks. The maximum (or minimum) value
never exceeds 0.999990 (or -0.999990), due to the number of variants used to
compute the quantiles (~300K). Because of this, we recommend using quantile
scores as an indicator of whether the raw score is unusually large, and use the
'raw scores' as a measure of magnitude of the effect for a given scorer and
track.

For signed variant scores (which indicate effect direction like up-regulation or
down-regulation), their [0,1] quantile probabilities – derived directly from the
rank order of the original signed raw scores – are linearly transformed to a
[-1,1] range. This rescaling ensures the quantile score reflects the
directionality of the raw score. For instance, the 0th percentile (representing
the most negative raw scores) maps to -1, the 50th percentile (raw scores around
zero) to 0, and the 100th percentile (most positive raw scores) to +1.

Note that quantile scores are only available for the suite of recommended
scorers.

## Other

### What terms of use apply to AlphaGenome outputs?

The AlphaGenome API is provided for non-commercial use only and is subject to
the AlphaGenome
[Terms of Service](https://deepmind.google.com/science/alphagenome/terms).
Outputs generated by AlphaGenome should not be used for the training of other
machine learning models.

### How should I cite AlphaGenome?

If you use AlphaGenome in your research, please cite using:

<!-- disableFinding(SNIPPET_INVALID_LANGUAGE) -->

```bibtex
@article{alphagenome,
  title={{AlphaGenome}: advancing regulatory variant effect prediction with a unified {DNA} sequence model},
  author={Avsec, {\v Z}iga and Latysheva, Natasha and Cheng, Jun and Novati, Guido and Taylor, Kyle R. and Ward, Tom and Bycroft, Clare and Nicolaisen, Lauren and Arvaniti, Eirini and Pan, Joshua and Thomas, Raina and Dutordoir, Vincent and Perino, Matteo and De, Soham and Karollus, Alexander and Gayoso, Adam and Sargeant, Toby and Mottram, Anne and Wong, Lai Hong and Drot{\'a}r, Pavol and Kosiorek, Adam and Senior, Andrew and Tanburn, Richard and Applebaum, Taylor and Basu, Souradeep and Hassabis, Demis and Kohli, Pushmeet},
  year={2025},
  doi={https://doi.org/10.1101/2025.06.25.661532},
  publisher={Cold Spring Harbor Laboratory},
  journal={bioRxiv}
}
```

<!-- enableFinding(SNIPPET_INVALID_LANGUAGE) -->

### Who should I contact with issues, enquiries and feedback?

Submit bugs and any code-related issues on
[GitHub](https://github.com/google-deepmind/alphagenome). For general feedback,
questions about usage, and/or feature requests, please use the
[community forum](https://www.alphagenomecommunity.com) – it's actively
monitored by our team so you're likely to find answers and insights faster. If
you can't find what you're looking for, please get in touch with the AlphaGenome
team at <alphagenome@google.com> and we will be happy to assist you with
questions. We're working hard to answer all inquiries but there may be a short
delay in our response due to the high volume we are receiving.
