#!/usr/bin/env Rscript
# Phase A -- phylogenetic signal in module conservation.
# Blomberg's K (1000-perm null) + Pagel's lambda (LR test) per module,
# treating each module's per-species Zsummary as a continuous trait on a
# TimeTree-calibrated ultrametric species tree.
suppressMessages({library(ape); library(phytools)})
tr <- read.tree("data/species_tree.nwk")
if (!is.ultrametric(tr)) tr <- force.ultrametric(tr, method="nnls")
W  <- read.csv("results/phaseA_trait_matrix.csv", row.names=1, check.names=FALSE)
res <- data.frame()
for (m in colnames(W)) {
  x <- W[[m]]; names(x) <- rownames(W); x <- x[!is.na(x)]
  tt <- keep.tip(tr, intersect(names(x), tr$tip.label)); x <- x[tt$tip.label]
  if (length(x) < 5) next
  k <- phylosig(tt, x, method="K", test=TRUE, nsim=1000)
  l <- phylosig(tt, x, method="lambda", test=TRUE)
  res <- rbind(res, data.frame(module=m, n=length(x), K=k$K, K_p=k$P,
                               lambda=l$lambda, lambda_p=l$P))
}
write.csv(res, "results/phaseA_phylo_signal.csv", row.names=FALSE)
