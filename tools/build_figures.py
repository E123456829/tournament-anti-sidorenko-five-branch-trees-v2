"""Export the six unchanged editable diagrams as standalone vector PDFs.

Requires the same LuaLaTeX/latexmk runtime as build_views.py, plus the standard
standalone/TikZ packages. Existing exported PDFs suffice to build the paper.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from build_views import compile_job

PREAMBLE = r'''\documentclass[11pt,tikz,border=3pt]{standalone}
\usepackage{fontspec}
\setmainfont{texgyretermes-regular.otf}[Path=fonts/,BoldFont=texgyretermes-bold.otf,ItalicFont=texgyretermes-italic.otf,BoldItalicFont=texgyretermes-bolditalic.otf]
\usepackage{amsmath,amssymb,unicode-math}
\setmathfont{latinmodern-math.otf}[Path=fonts/]
\usetikzlibrary{arrows.meta,positioning,fit}
\newcommand{\E}{\mathbb E}
\newcommand{\one}{\mathbf1}
\newcommand{\ip}[2]{\left\langle#1,#2\right\rangle}
\newcommand{\norm}[1]{\left\lVert#1\right\rVert}
\newcommand{\homc}{\operatorname{hom}}
\begin{document}
\input{diagram}
\end{document}
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    source, work = args.source.resolve(), args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    figures = sorted((source / 'figures').glob('*.tex'))
    if len(figures) != 6:
        raise RuntimeError('Expected the six manuscript diagrams')
    rows = []
    for figure in figures:
        folder = work / figure.stem
        folder.mkdir(exist_ok=True)
        shutil.copytree(source / 'fonts', folder / 'fonts', dirs_exist_ok=True)
        shutil.copyfile(figure, folder / 'diagram.tex')
        (folder / 'figure.tex').write_text(PREAMBLE, encoding='utf-8')
        record = compile_job(folder, 'figure')
        target = figure.with_suffix('.pdf')
        shutil.copyfile(folder / 'figure.pdf', target)
        rows.append(dict(source=figure.relative_to(source).as_posix(),
            source_sha256=hashlib.sha256(figure.read_bytes()).hexdigest(),
            graphic=target.relative_to(source).as_posix(),
            graphic_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            build=record))
    (work / 'FIGURE_EXPORT_REPORT.json').write_text(json.dumps(dict(figures=rows,
        source_content_changed=False), indent=2) + '\n', encoding='utf-8')
    print('Six vector figures exported.', flush=True)

if __name__ == '__main__':
    main()
