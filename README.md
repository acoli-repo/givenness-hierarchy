# Revisiting the Givenness Hierarchy

Experiments for the corpus-based replication of Gundel et al. (1993)'s Givenness Hierarchy over all 7 languages originally considered by Gundel et al. (1990) and Gundel et al. (1993) as described in

> Christian Chiarcos (2025), [Revisiting the Givenness Hierarchy. A Corpus-Based Evaluation](https://aclanthology.org/2025.crac-1.3/). In Proceedings of the Eighth Workshop on Computational Models of Reference, Anaphora and Coreference (CRAC 2025), held in conjunction with EMNLP-2025, Souzhou, China, Nov 9th, 2025, Association of Computational Linguistics, p.24-41 [https://aclanthology.org/2025.crac-1.3/](https://aclanthology.org/2025.crac-1.3/)

## Content

Please check out our [overview video at Youtube](https://youtu.be/za0pEDJHmRk).

This repo includes

- **code**: build and extraction scripts for OntoNotes and CorefUD formats (see `scripts/`)
- **code**: build scripts to convert the Japanese NTC 1.5 corpus and the Korean KoCoNovel to CorefUD (see `data/jp` and `data/ko`)
- **data**: mirrors of all CorefUD 1.3 corpora for English, Korean, Russian, Spanish (see `data/`)
- **documentation**: [paper](doc/givenness-2025.paper.pdf), [slides](doc/givenness-2025.slides.pdf), [poster](doc/givenness-2025.poster.pdf), and [BibTex](doc/givenness-2025.bib)

This repo does *not* include

- OntoNotes corpora for Arabic, English and Chinese. You can get these (currently for free) from https://catalog.ldc.upenn.edu/LDC2013T19. We do, however, provide data extracted from OntoNotes, as copyright restrictions do not apply to these excerpts -- as they neither allow to reconstruct any single line of the original text nor any original annotations.

## Usage conditions

- Our code (`Makefile`s, and `scripts/`) is licensed under [LICENSE](Apache licence 2.0). When using these files or our CorefUD conversions of the Korean KoCoNovel or the Japanese NTC 1.5 corpora included, we request reference to the following paper

	> Christian Chiarcos (2025), Revisiting the Givenness Hierarchy. A Corpus-Based Evaluation. In Proceedings of the Eighth Workshop on Computational Models of Reference, Anaphora and Coreference (CRAC 2025), held in conjunction with EMNLP-2025, Souzhou, China, Nov 9th, 2025, Association of Computational Linguistics, p.24-41

- The source corpora come under their own licenses, see under `data/`. Except for OntoNotes data, redistribution is permitted.
- As for the extracted data, this is provided for convenience only and *should be re-built by the user*.

## Contributors

Code and experiments were primarily developed by Christian Chiarcos, University of Augsburg, Germany, with support by Stefan Radle (for Japanese) and Mahmud Uz-Zaman (for Arabic).
