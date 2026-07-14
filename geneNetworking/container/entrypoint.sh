#!/usr/bin/env bash
# =============================================================================
# geneNetworking container entrypoint — dispatches into the right conda env.
# =============================================================================
# Usage (all invoked as `docker compose run --rm gn <SUBCOMMAND> ...`):
#
#   help                       show this message
#   envs                       list the three conda environments
#   shell [env]                interactive bash inside <env> (default: coexpr)
#
#   coexpr   <cmd...>          run a command in the Python main-pipeline env
#   wgcna-r  <cmd...>          run a command in the R WGCNA / phylo env
#   pyscenic <cmd...>          run a command in the single-cell pySCENIC env
#
#   wgcna    <args...>         shortcut: canonical R WGCNA driver
#                              (= wgcna-r Rscript R/01_wgcna_modules.R <args>)
#   phylo                      shortcut: Phase A phylo-signal
#                              (= wgcna-r Rscript scripts/05_phaseA_phylo_signal.R)
#   py       <script.py> ...   shortcut: run a scripts/*.py in the coexpr env
#
# Examples:
#   docker compose run --rm gn envs
#   docker compose run --rm gn wgcna --input results/wgcna_input.tsv --outdir results
#   docker compose run --rm gn py scripts/08_grn_ensemble.py
#   docker compose run --rm gn wgcna-r Rscript -e 'packageVersion("WGCNA")'
#   docker compose run --rm gn shell coexpr
# =============================================================================
set -euo pipefail

REPO=/opt/geneNetworking
run() { exec micromamba run -n "$1" "${@:2}"; }

cmd="${1:-help}"; shift || true

case "$cmd" in
  help|--help|-h|"")
    # print the leading comment block (lines 2.. up to the first non-# line)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    ;;

  envs)
    micromamba env list
    ;;

  shell)
    env="${1:-coexpr}"
    exec micromamba run -n "$env" bash
    ;;

  # ---- raw env passthroughs ----
  coexpr|wgcna-r|pyscenic)
    if [ "$#" -eq 0 ]; then exec micromamba run -n "$cmd" bash; fi
    run "$cmd" "$@"
    ;;

  # ---- convenience shortcuts ----
  wgcna)
    run wgcna-r Rscript "$REPO/R/01_wgcna_modules.R" "$@"
    ;;

  phylo)
    run wgcna-r Rscript "$REPO/scripts/05_phaseA_phylo_signal.R" "$@"
    ;;

  py)
    run coexpr python "$@"
    ;;

  *)
    echo "Unknown subcommand: $cmd" >&2
    echo "Run 'help' for usage." >&2
    exit 2
    ;;
esac
