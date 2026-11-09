@echo off
rem Clean all LaTeX temp files, then build SDP1_Report_Group34_v12.pdf from scratch.
rem Double-click this file, or run it from any folder.
setlocal
cd /d "%~dp0"
set "J=SDP1_Report_Group34_v12"
set "TEXINPUTS=.;./Template;"

echo === Cleaning temp files ===
for %%E in (acn acr alg aux bbl blg glg glo gls ist loc lof log lot out soc toc synctex.gz fls fdb_latexmk) do (
    if exist "%J%.%%E" del /q "%J%.%%E"
)
if exist "Template\abstract_ar.aux" del /q "Template\abstract_ar.aux"
if exist "Template\abstract_ar.log" del /q "Template\abstract_ar.log"

echo === [0/5] Short reference keys (tools\make_refshort.py) ===
where python >nul 2>&1 && python tools\make_refshort.py

echo === [1/5] Arabic abstract (lualatex) ===
pushd Template
lualatex -interaction=nonstopmode abstract_ar.tex >nul 2>&1
if errorlevel 1 echo   WARNING: abstract_ar.tex had errors - see Template\abstract_ar.log
popd

echo === [2/5] pdflatex pass 1 ===
pdflatex -interaction=nonstopmode -jobname=%J% Template/Proposal.tex >nul 2>&1

echo === [3/5] bibtex + glossaries ===
bibtex %J% >nul 2>&1
makeglossaries-lite %J% >nul 2>&1 || makeglossaries %J% >nul 2>&1

echo === [4/5] pdflatex pass 2 ===
pdflatex -interaction=nonstopmode -jobname=%J% Template/Proposal.tex >nul 2>&1

echo === [5/5] pdflatex pass 3 ===
pdflatex -interaction=nonstopmode -jobname=%J% Template/Proposal.tex >nul 2>&1
echo === [5/5] pdflatex pass 4 (bibliography back-links) ===
pdflatex -interaction=nonstopmode -jobname=%J% Template/Proposal.tex >nul 2>&1

echo.
echo === Errors (lines starting with "!" in %J%.log) ===
findstr /b /n /c:"!" "%J%.log"
if errorlevel 1 echo   none

echo.
if exist "%J%.pdf" (echo Built %J%.pdf) else (echo BUILD FAILED - no PDF produced, check %J%.log)
endlocal
pause
