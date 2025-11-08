# Summary

English-ParCorFull is a conversion of the English part of ParCorFull, an English-German
parallel corpus annotated with coreference. Due to their non-derivative license,
TED-talks have been excluded from the conversion.

## References

```
@misc{ParCorFull,
    title = {{ParCorFull}: A Parallel Corpus Annotated with Full Coreference},
    author = {Lapshinova-Koltunski, Ekaterina and Hardmeier, Christian and Krielke, Pauline},
    url = {http://hdl.handle.net/11372/LRT-2614},
    note = {{LINDAT}/{CLARIAH}-{CZ} digital library at the Institute of Formal and Applied Linguistics ({{\'U}FAL}), Faculty of Mathematics and Physics, Charles University},
    copyright = {Creative Commons - Attribution-{NonCommercial}-{NoDerivatives} 4.0 International ({CC} {BY}-{NC}-{ND} 4.0)},
    year = {2018}
}

@inproceedings{ParCorFull-paper,
    author = {Ekaterina Lapshinova-Koltunski and Christian Hardmeier and Pauline Krielke},
    title = {{ParCorFull: a Parallel Corpus Annotated with Full Coreference}},
    booktitle = {Proceedings of the Eleventh International Conference on Language Resources and Evaluation (LREC 2018)},
    publisher = {European Language Resources Association (ELRA)},
    address = {Miyazaki, Japan},
    year = {2018},
    pages - {423--428},
}
```

# Changelog

### 2023-02-24 v1.1
  * fix import, so that markables are detected even in invalid files
    with extra `<html><body>` elements:
    03_words.xml (train), 20_words.xml (train), 25_words.xml (test)
  * morpho-syntactic attributes updated using UD 2.10 models
### 2022-04-06 v1.0
  * new format of coreference and anaphora annotations
### 2021-12-10 v0.2
  * morpho-syntactic attributes updated using UDPipe 2 with UD 2.6 models
### 2021-03-11 v0.1
  * initial conversion

```
=== Machine-readable metadata (DO NOT REMOVE!) ================================
Data available since: CorefUD 0.1
License: CC BY-NC 4.0
Includes text: yes
Genre: news
Lemmas: automatic
UPOS: automatic
XPOS: automatic
Features: automatic
Relations: automatic
CorefUD contributors: Lapshinova-Koltunski, Ekaterina (1); Hardmeier, Christian (2); Krielke, Pauline (1)
Other contributors:
Contributors' affiliations: (1) Saarland University, Department of Language Science and Technology, Saarbrücken, Germany
                            (2) Uppsala University, Department of Linguistics and Philology, Uppsala, Sweden
Contributing: elsewhere
Contact: e.lapshinova@mx.uni-saarland.de
===============================================================================
```
