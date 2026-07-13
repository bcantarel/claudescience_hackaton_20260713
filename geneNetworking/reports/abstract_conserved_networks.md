# Conserved gene co-expression & regulatory networks across vertebrates — abstract

One of the holy grails of biology is to understand how 1 genome can make all the
different cell types, each with a unique regulatory network. While these questions are
starting to be answered in model organisms such as the mouse and human, it's unclear if
these regulatory networks are conserved across species in the same cell types. If these
networks are conserved across species, then gene regulatory networks found in model
organisms are conserved and can be used to predict genotype-to-phenotype relationships
in other mammals or vertebrates. However, if the same transcription factors are not
regulating the same genes in the same cell types, then data must be collected in distant
organisms.

Using both bulk-RNASeq and scRNASeq, we found that a conserved core — but not all — of
the gene co-expression networks is preserved across 26 vertebrate species spanning humans
to zebrafish, representing ~430 million years of evolution. Starting from a well-powered
human reference (GTEx, 30 tissues), we discovered 27 tissue-defining co-expression
modules and tested their preservation across the vertebrate tree. The modules split
cleanly into two classes: a core set of programs — neuronal-synaptic (brain), meiotic
(testis), oogenic (ovary), contractile (muscle) and immune — that is conserved essentially
everywhere, and a labile set — pancreatic, adipose and lung — that is not. Strikingly,
conservation is governed by which program a network belongs to, not by how long ago two
species diverged (preservation vs. divergence time Spearman rho = -0.24, n.s.; Blomberg's
K << 1 for the conserved core), implying that these core programs are held in place by
deep stabilizing selection acting across all lineages at once rather than eroding
gradually with evolutionary distance. Within each conserved module, gene membership is
preserved while the fine-scale hub wiring drifts — a pattern we confirmed at single-cell
resolution (Tabula Sapiens / Muris / Microcebus for human, mouse and lemur, plus a
zebrafish outgroup): the identity of the master regulators is the conserved axis
(regulator-identity conservation 0.42), while their downstream target sets are the labile
one (0.17). The conserved regulator core reaches all the way to teleost fish — MEF2
(muscle), SPI1/PU.1 and IKZF1 (immune), and EBF3/PBX (neuron) recur as top regulators in
zebrafish (permutation p <= 0.016) — which brackets the intervening marsupial and
afrotherian lineages.

We discovered transcription factors that regulate different genes, depending on the
presence of other transcription factors — combinatorial "cocktails" recovered purely from
co-expression (e.g. hepatocyte HNF1A+HNF4A+HNF1B, immune IKZF1xSPI1, testis FOXM1xE2F2).
Critically, single-cell data showed that the same TF pair can act as a genuine
co-regulator in one species or cell type and as a cell-composition artifact in another
(e.g. IKZF1xIRF4 is a genuine plasma-cell cocktail only in lemur), demonstrating that
combinatorial regulatory logic is itself context-dependent across species.

These results argue that gene regulatory networks discovered in model organisms are, for
the conserved core, transferable — master-regulator identity can be used to predict
genotype-to-phenotype relationships across mammals and vertebrates — while a minority of
labile, clade-variable programs (notably the KRAB-zinc-finger-rich pituitary and adipose
modules) will require data collected directly in the target organisms. This work
represents a limited pilot; additional data in more distantly related and undersampled
vertebrates (marsupials such as koala and Tasmanian devil, and afrotherians) is needed to
determine precisely which networks remain conserved under which master regulators.
