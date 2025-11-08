# Arabic OntoNotes

To run the OntoNotes extractor from scratch, deposit the content of Arabic OntoNotes under `ontonotes-release-5.0/annotation/` and `ontonotes-release-5.0/metadata/` in this directory.

As for the classification of referring expressions, we operate with a json dict, extracted from OntoNotes and other sources by Christian Chiarcos, and manually curated by Mahmud Uz-Zaman, University of Augsburg, Gemany. Note that this needs to be double-checked by a native speaker. This has been integrated into ../scripts/config.json which defines extraction and classification patterns for Gundel-style referring expressions.