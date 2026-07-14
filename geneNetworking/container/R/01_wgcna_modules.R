#!/usr/bin/env Rscript
# =============================================================================
# Stage 1 — WGCNA module discovery with the CANONICAL R WGCNA package.
# =============================================================================
# This is the original-implementation counterpart to the repo's pure-Python
# reimplementation (scripts/02_wgcna_modules.py). That reimplementation exists
# only because bioconda ships no osx-arm64 build of r-wgcna; inside this
# linux-64 container the canonical Langfelder & Horvath (2008) WGCNA package
# runs, so the two routes can be compared head to head.
#
# Method (identical parameters to 02_wgcna_modules.py):
#   signed-hybrid adjacency, soft power beta = 8
#   -> signed TOM  ->  average-linkage hclust on (1 - TOM)
#   -> cutreeDynamic (hybrid): minClusterSize = 30, deepSplit = 2, pamStage = FALSE
#   -> mergeCloseModules at mergeCutHeight = 0.25  (== eigengene corr > 0.75)
#
# Input : a genes x samples matrix (TSV; first column = gene id, header =
#         sample ids), log2-CPM, already variance-filtered to ~14,000 genes.
#         Produce it from the existing wgcna_input.pkl with:
#             tools/pkl_to_tsv.py wgcna_input.pkl wgcna_input.tsv
#
# Output (into --outdir):
#   stage1_gene_modules_R.csv   ensembl_gene, module (colour + integer label)
#   module_eigengenes_R.csv     samples x module-eigengene matrix (post-merge)
#   wgcna_softthreshold_R.png   scale-free-fit / mean-connectivity QC (2-panel)
#   wgcna_dendrogram_R.png      gene dendrogram + dynamic/merged module colours
#   wgcna_run_R.log             parameters + module size table (provenance)
# =============================================================================

suppressMessages({
  library(optparse)
  library(WGCNA)
  library(data.table)
})

# WGCNA's own guidance; harmless in a container but required for its internals.
options(stringsAsFactors = FALSE)
enableWGCNAThreads()

# ---- CLI -------------------------------------------------------------------
opt_list <- list(
  make_option("--input",   type = "character",
              help = "genes x samples TSV (col1 = gene id, header = sample ids)"),
  make_option("--outdir",  type = "character", default = "results",
              help = "output directory [default %default]"),
  make_option("--power",   type = "integer",   default = 8L,
              help = "soft-thresholding power beta [default %default]"),
  make_option("--minsize", type = "integer",   default = 30L,
              help = "minModuleSize for cutreeDynamic [default %default]"),
  make_option("--deepsplit", type = "integer", default = 2L,
              help = "deepSplit 0-4 [default %default]"),
  make_option("--mergecut", type = "double",   default = 0.25,
              help = "mergeCutHeight (1 - eigengene corr) [default %default]"),
  make_option("--sweep-power", action = "store_true", default = FALSE,
              help = "only run pickSoftThreshold sweep + QC plot, then exit")
)
opt <- parse_args(OptionParser(option_list = opt_list))
if (is.null(opt$input)) stop("--input is required")
dir.create(opt$outdir, showWarnings = FALSE, recursive = TRUE)
logf <- file.path(opt$outdir, "wgcna_run_R.log")
say  <- function(...) { msg <- paste0(...); cat(msg, "\n"); cat(msg, "\n", file = logf, append = TRUE) }
cat("", file = logf)  # truncate log

# ---- load matrix -----------------------------------------------------------
say("[load] reading ", opt$input)
mat <- as.data.frame(fread(opt$input, header = TRUE))
rownames(mat) <- mat[[1]]; mat[[1]] <- NULL
mat <- as.matrix(mat)
say("[load] genes x samples = ", nrow(mat), " x ", ncol(mat))

# WGCNA expects samples in ROWS, genes in COLUMNS
datExpr <- t(mat)

# QC: drop genes/samples with too many missing / zero-variance entries
gsg <- goodSamplesGenes(datExpr, verbose = 0)
if (!gsg$allOK) {
  say("[qc] removing ", sum(!gsg$goodGenes), " genes / ",
      sum(!gsg$goodSamples), " samples flagged by goodSamplesGenes")
  datExpr <- datExpr[gsg$goodSamples, gsg$goodGenes]
}
say("[qc] final samples x genes = ", nrow(datExpr), " x ", ncol(datExpr))

# ---- soft-threshold sweep (QC + optional early exit) -----------------------
powers <- c(1:10, seq(12, 20, 2))
sft <- pickSoftThreshold(datExpr, powerVector = powers,
                         networkType = "signed hybrid", verbose = 0)
say("[sft] estimated power (R^2>=0.85) = ",
    ifelse(is.na(sft$powerEstimate), "NA (using --power)", sft$powerEstimate))

png(file.path(opt$outdir, "wgcna_softthreshold_R.png"),
    width = 1200, height = 500, res = 120)
par(mfrow = c(1, 2))
fit <- -sign(sft$fitIndices[, 3]) * sft$fitIndices[, 2]
plot(sft$fitIndices[, 1], fit, type = "n",
     xlab = "soft power beta", ylab = "scale-free fit R^2",
     main = "Scale-free topology fit")
text(sft$fitIndices[, 1], fit, labels = powers, col = "red")
abline(h = 0.85, col = "blue", lty = 2)
abline(v = opt$power, col = "darkgreen", lty = 3)
plot(sft$fitIndices[, 1], sft$fitIndices[, 5], type = "n",
     xlab = "soft power beta", ylab = "mean connectivity",
     main = "Mean connectivity")
text(sft$fitIndices[, 1], sft$fitIndices[, 5], labels = powers, col = "red")
abline(v = opt$power, col = "darkgreen", lty = 3)
dev.off()
say("[sft] wrote wgcna_softthreshold_R.png")

if (opt$`sweep-power`) { say("[done] sweep-only mode; exiting"); quit(status = 0) }

# ---- adjacency -> signed TOM -----------------------------------------------
beta <- opt$power
say("[net] signed-hybrid adjacency at beta = ", beta)
adj <- adjacency(datExpr, power = beta, type = "signed hybrid")
say("[net] signed TOM")
TOM     <- TOMsimilarity(adj, TOMType = "signed")
dissTOM <- 1 - TOM
rm(adj); gc()

# ---- hierarchical clustering + dynamic tree cut ----------------------------
say("[clust] average-linkage hclust on (1 - TOM)")
geneTree <- hclust(as.dist(dissTOM), method = "average")

say("[clust] cutreeDynamic hybrid: minSize=", opt$minsize,
    " deepSplit=", opt$deepsplit, " pamStage=FALSE")
dynMods <- cutreeDynamic(dendro = geneTree, distM = dissTOM,
                         method = "hybrid", deepSplit = opt$deepsplit,
                         pamStage = FALSE, minClusterSize = opt$minsize)
dynColors <- labels2colors(dynMods)
say("[clust] pre-merge modules (incl. grey) = ", length(unique(dynColors)))

# ---- merge close modules by eigengene correlation --------------------------
say("[merge] mergeCloseModules at mergeCutHeight = ", opt$mergecut,
    " (eigengene corr > ", 1 - opt$mergecut, ")")
merge <- mergeCloseModules(datExpr, dynColors,
                           cutHeight = opt$mergecut, verbose = 0)
mergedColors <- merge$colors
MEs          <- merge$newMEs
nMod <- length(setdiff(unique(mergedColors), "grey"))
say("[merge] post-merge modules (excl. grey) = ", nMod)

# ---- dendrogram QC plot ----------------------------------------------------
png(file.path(opt$outdir, "wgcna_dendrogram_R.png"),
    width = 1400, height = 700, res = 120)
plotDendroAndColors(geneTree,
                    cbind(dynColors, mergedColors),
                    c("Dynamic", "Merged"),
                    dendroLabels = FALSE, hang = 0.03,
                    addGuide = TRUE, guideHang = 0.05,
                    main = paste0("Gene dendrogram & module colours (beta=", beta, ")"))
dev.off()
say("[plot] wrote wgcna_dendrogram_R.png")

# ---- write outputs ---------------------------------------------------------
# integer label per colour (grey = 0), for parity with the Python labels
colOrder <- c("grey", setdiff(names(sort(table(mergedColors), decreasing = TRUE)), "grey"))
lab      <- match(mergedColors, colOrder) - 1L
out <- data.frame(ensembl_gene = colnames(datExpr),
                  module_color = mergedColors,
                  module       = lab)
fwrite(out, file.path(opt$outdir, "stage1_gene_modules_R.csv"))
say("[out] wrote stage1_gene_modules_R.csv (", nrow(out), " genes)")

me_out <- data.frame(sample = rownames(MEs), MEs, check.names = FALSE)
fwrite(me_out, file.path(opt$outdir, "module_eigengenes_R.csv"))
say("[out] wrote module_eigengenes_R.csv (", ncol(MEs), " eigengenes)")

# module size table -> log (provenance)
tab <- as.data.frame(sort(table(mergedColors), decreasing = TRUE))
colnames(tab) <- c("module_color", "n_genes")
say("[summary] module sizes:")
for (i in seq_len(nrow(tab)))
  say("           ", tab$module_color[i], "\t", tab$n_genes[i])
say("[done] Stage 1 (canonical R WGCNA) complete -> ", opt$outdir)
