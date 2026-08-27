#!/bin/bash
set -euo pipefail

echo "=== Strelka smoke test ==="

: "${EBROOTSTRELKA:?EBROOTSTRELKA is not set}"

echo "Strelka root: $EBROOTSTRELKA"
echo "Python: $(python --version 2>&1)"

python -c 'import sys; assert sys.version_info[:2] == (2, 7), sys.version'

test -x "$EBROOTSTRELKA/bin/configureStrelkaGermlineWorkflow.py"
test -x "$EBROOTSTRELKA/bin/configureStrelkaSomaticWorkflow.py"
test -f "$EBROOTSTRELKA/bin/runStrelkaGermlineWorkflowDemo.bash"
test -f "$EBROOTSTRELKA/bin/runStrelkaSomaticWorkflowDemo.bash"

"$EBROOTSTRELKA/bin/configureStrelkaGermlineWorkflow.py" --help >/dev/null
"$EBROOTSTRELKA/bin/configureStrelkaSomaticWorkflow.py" --help >/dev/null

workdir=$(mktemp -d "${TMPDIR:-/tmp}/strelka-smoketest.XXXXXX")
trap 'rm -rf "$workdir"' EXIT

cd "$workdir"

echo
echo "=== Germline workflow demo ==="
bash "$EBROOTSTRELKA/bin/runStrelkaGermlineWorkflowDemo.bash"

test -f strelkaGermlineDemoAnalysis/results/variants/variants.vcf.gz
gzip -t strelkaGermlineDemoAnalysis/results/variants/variants.vcf.gz

echo
echo "=== Somatic workflow demo ==="
bash "$EBROOTSTRELKA/bin/runStrelkaSomaticWorkflowDemo.bash"

test -f strelkaSomaticDemoAnalysis/results/variants/somatic.snvs.vcf.gz
test -f strelkaSomaticDemoAnalysis/results/variants/somatic.indels.vcf.gz
gzip -t strelkaSomaticDemoAnalysis/results/variants/somatic.snvs.vcf.gz
gzip -t strelkaSomaticDemoAnalysis/results/variants/somatic.indels.vcf.gz

echo
echo "=== Strelka smoke test PASSED ==="