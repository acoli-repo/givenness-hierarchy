# Addenda for Givenness Hierarchy experiments

- `corefud/` CorefUD-compatible version created from the merging of `data/` with UDPipe (korean-kaist-ud-2.5-191206) parses
- to build from scratch
	- deposit directories with CoNLL-U parses in `ud/`
	- run

		```
		$> cd ud
		$> make
		```

Note that we *assume* that this corpus is under CC BY-SA 4.0 (because its source material entails a Share-Alike term), but we asked the authors for an explicit confirmation, check status under the corresponding [GitHub issue](https://github.com/storidient/KoCoNovel/issues/1).

If this is not to be confirmed, the corpus will be withdrawn.