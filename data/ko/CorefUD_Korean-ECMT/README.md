# Summary

Korean-ECMT is a conversion of the dataset created for the paper "Effective Crowdsourcing of Multiple Tasks for Comprehensive Knowledge Extraction" (ECMT).
The original dataset is based on Korean Wikipedia and KBox with crowdsourced annotations for four information extraction tasks: (1) entity detection, (2) entity linking, (3) coreference resolution, and (4) relation extraction.

The dataset is provided as JSON files that capture different stages of the annotation process (https://figshare.com/s/7367aeca244efae03068).
Additionally, a CoNLL-2012 conversion of the coreference annotations was created by one of the paper's co-authors (https://github.com/machinereading/CR/tree/master/input).
However, this CoNLL-2012 version has several limitations.
It does not include the original detokenized sentences.
It follows tokenization rules incompatible with any of the Korean datasets in UD, making annotation mapping difficult.
It does not retain singleton entity annotations.
Due to these issues, the CorefUD conversion is based on the original crowdsourcing JSON files, despite their lack of documentation.

A limitation of using the JSON files as the source is that they do not include the documents used to create the `whole.korean8_pd_NER.v4_gold_conll` file in the CoNLL-2012 conversion, which appears to be the test set.
As a result, we created a new train/dev/test split based on the available JSON documents.

Additionally, the original dataset contains errors where distinct entities are incorrectly merged into a single coreference cluster.
The CorefUD conversion did not attempt to fix these errors.

## References

```
@inproceedings{nam-etal-2020-effective,
    title = "Effective Crowdsourcing of Multiple Tasks for Comprehensive Knowledge Extraction",
    author = "Nam, Sangha  and
      Lee, Minho  and
      Kim, Donghwan  and
      Han, Kijong  and
      Kim, Kuntae  and
      Yoon, Sooji  and
      Kim, Eun-kyung  and
      Choi, Key-Sun",
    booktitle = "Proceedings of the Twelfth Language Resources and Evaluation Conference",
    month = may,
    year = "2020",
    address = "Marseille, France",
    publisher = "European Language Resources Association",
    url = "https://aclanthology.org/2020.lrec-1.27",
    pages = "212--219",
    language = "English",
    ISBN = "979-10-95546-34-4",
}
```

# Changelog

### 2025-04-17 v1.3
  * initial conversion
  * morpho-syntactic attributes produced by UDPipe 2 using UD 2.15 models

```
=== Machine-readable metadata (DO NOT REMOVE!) ================================
Data available since: CorefUD 1.3
License: CC BY 4.0
Includes text: yes
Genre: Wikipedia
Lemmas: automatic
UPOS: automatic
XPOS: automatic
Features: automatic
Relations: automatic
CorefUD contributors: Nam, Sangha (1); Novák, Michal (2); Porada, Ian (3)
Other contributors: Lee, Minho; Kim, Donghwan; Han, Kijong; Kim, Kuntae; Yoon, Sooji; Kim, Eun-kyung; Choi, Key-Sun
Contributors' affiliations: (1) KAIST, School of Computing, Daejeon, South Korea
                            (2) Charles University, Faculty of Mathematics and Physics, Institute of Formal and Applied Linguistics, Prague, Czechia
                            (3) Mila, McGill University, Montreal, Canada
Contributing: elsewhere
Contact: mnovak@ufal.mff.cuni.cz
===============================================================================
```
