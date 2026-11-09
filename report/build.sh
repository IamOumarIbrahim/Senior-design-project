#!/usr/bin/env bash
# Build the report from the project root (paths in the .tex are root-relative, as on Overleaf).
set -e
cd "$(dirname "$0")"
export TEXINPUTS=".;./Template;"
J=SDP1_Report_Group34_v12
( cd Template && lualatex -interaction=nonstopmode abstract_ar.tex >/dev/null )
pdflatex -interaction=nonstopmode -jobname=$J Template/Proposal.tex >/dev/null || true
bibtex $J >/dev/null || true
makeglossaries-lite $J >/dev/null || makeglossaries $J >/dev/null || true
pdflatex -interaction=nonstopmode -jobname=$J Template/Proposal.tex >/dev/null || true
pdflatex -interaction=nonstopmode -jobname=$J Template/Proposal.tex >/dev/null || true
pdflatex -interaction=nonstopmode -jobname=$J Template/Proposal.tex >/dev/null || true   # 4th pass: back-links
grep -E "^!" -A3 $J.log | head -40 || true
echo "built $J.pdf"
