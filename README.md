# Q4/Q5 research compendium, 2026.10.30-r2

This repository accompanies **Tournament anti-Sidorenko orientations of trees
with at most five branch vertices**, by Yanbin Qiao and Liwei Yao. It provides
the English manuscript, all necessary technical proofs, editable sources,
vector figures, rational certificate data and check/build tools.

## Versioned release and citation

[Download the release and checksum](https://github.com/E123456829/tournament-anti-sidorenko-five-branch-trees-v2/releases/tag/v2026.10.30-r2).

This repository supersedes the earlier public compendium at
`E123456829/tournament-anti-sidorenko-five-branch-trees`. It restores the
complete AI-assistance disclosure that had been shortened in the earlier r1
release; the mathematical content is unchanged from r1. The release asset
`Q4_Q5_Public_Archive_2026-10-30-r2.zip` is the exact package for this version; its SHA-256 digest is
recorded in the accompanying `.zip.sha256` sidecar and in the
repository-root `ARCHIVE_RECEIPT.json`. No DOI is assigned.

Suggested citation: Yanbin Qiao and Liwei Yao, *Tournament anti-Sidorenko
orientations of trees with at most five branch vertices: research compendium*,
version 2026.10.30-r2, GitHub, https://github.com/E123456829/tournament-anti-sidorenko-five-branch-trees-v2/releases/tag/v2026.10.30-r2.

This is a research manuscript and its reproducibility materials. Repository
publication does not imply journal acceptance or a formal verification of the
whole analytic proof. No general open-content or open-source licence has been
assigned; see RIGHTS.md for the current licensing status.

The three PDFs are reading views of the same mathematical manuscript:
01_Article.pdf (24 pages), 02_Technical_Appendix.pdf (1006 pages) and
03_Complete_Manuscript.pdf (1030 pages). Keep them together for companion links.
The appendices contain necessary proofs and must accompany the article.

The manuscript's AI-assistance declaration is in `paper/jgt/declarations.tex`
and reads: "AI assistance was used during symbolic exploration and manuscript
preparation: OpenAI Codex assisted with merging, translation and typesetting;
DeepSeek assisted with language editing and with language polishing and
typesetting of the final manuscript. The authors are responsible for the
content of this manuscript."

## Exact arithmetic

With Python 3.10 or newer, from the extracted root directory:

```
python tools/verify_certificates.py --data certificates/polynomial_certificates.json --check-source paper/jgt
```

This uses Python's standard library and exact fractions. It checks 243
closed-cell records, all 4345 rational Bernstein coefficients, forward and
reverse polynomial reconstruction, coefficient bounds and 25 source hashes.
The records subdivide scalar certificates; they are not 243 separate theorems.
The analytic reductions and tree orientations are proved in the manuscript.

## Build

Install a working LuaLaTeX distribution with latexmk, BibTeX, fontspec,
unicode-math, amsthm, xr-hyper, natbib, hyperref, graphicx and the other standard
packages named in main.tex. No Python dependency beyond the standard library
is required. pypdf is optional for page-count metadata.

```
python tools/build_views.py --source paper/jgt --work build --out build/pdf
```

The included figure PDFs suffice for this build. If a diagram is edited,
regenerate the figures first (also needs the standalone and TikZ packages):

```
python tools/build_figures.py --source paper/jgt --work build/figures
```

The build tool compiles all three views and refreshes companion-file references.
It does not install packages or download dependencies. Build duration depends
on the TeX installation and the length of the technical appendices.

indexes/ gives 100 numbered-statement locations and 149 local-proof file
locations. Page fields refer to the complete reading view, which is 1030 pages
in this version. These indexes are navigation aids, not proof certificates.
BUILD_INPUT_IDENTITY.json records the source, font and graphic identities of the
successful PDF build.

The repository-root SHA256SUMS covers every other tracked repository file. The release asset has its
own independently recorded SHA-256 digest in the sidecar. Internal review
correspondence, historical editing logs and local submission metadata are not
part of this public compendium. Reproducibility does not depend on those
private records.
