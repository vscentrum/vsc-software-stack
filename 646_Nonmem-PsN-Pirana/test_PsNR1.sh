#!/usr/bin/env bash
set -euo pipefail

echo "R: $(command -v R)"
echo "Rscript: $(command -v Rscript)"
echo "R_LIBS_SITE=${R_LIBS_SITE:-<unset>}"

Rscript --vanilla - <<'RSCRIPT'
pkgs <- c(
  "PsNR",
  "vpc", "xpose", "xpose4", "vegawidget", "PerformanceAnalytics", "vaplot",
  "dplyr", "tidyr", "purrr", "kableExtra", "sessioninfo", "yaml",
  "rmarkdown", "knitr", "ggforce", "stringr", "stringi", "RColorBrewer",
  "scales", "forcats", "MASS", "rlang", "labeling", "expm", "mvtnorm",
  "gridExtra", "magrittr", "ggplot2", "caTools", "formatR", "ggthemes",
  "gplots", "plyr", "tibble", "htmltools", "glue", "rjson"
)

cat("R version:", R.version.string, "\n")
cat(".libPaths():\n")
print(.libPaths())

missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop("Missing R packages: ", paste(missing, collapse = ", "))
}

suppressPackageStartupMessages(library(PsNR))

cat("Loaded PsNR version:", as.character(utils::packageVersion("PsNR")), "\n")

exports <- getNamespaceExports("PsNR")
cat("Number of exported PsNR objects:", length(exports), "\n")
if (!length(exports)) stop("PsNR loaded, but exports no objects")

cat("First exported PsNR objects:\n")
print(utils::head(sort(exports), 20))

renv_loaded <- "renv" %in% loadedNamespaces()
cat("renv loaded:", renv_loaded, "\n")
if (renv_loaded) stop("renv was loaded during the PsNR smoke test")

cat("PsNR smoke test OK\n")
RSCRIPT