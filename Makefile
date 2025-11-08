SHELL=bash

all: 
	@make build || \
	 (echo build failed, please run make prep first 1>&2; \
	  exit 3;)

build:
	@lang_tgt_srces="en:corefud-litbank.tsv:data/en/CorefUD_English-LitBank/ \
					 en:corefud-gum.tsv:data/en/CorefUD_English-GUM/ \
				   	 en:corefud-parcor.tsv:data/en/CorefUD_English-ParCorFull/ \
					 en:ontonotes.tsv:data/en/ontonotes-release-5.0/ \
					 es:ancora.tsv:data/es/CorefUD_Spanish-AnCora/ \
					 ru:rucor.tsv:data/ru/CorefUD_Russian-RuCor/ \
					 ar:ontonotes.tsv:data/ar/ontonotes-release-5.0/ \
					 zh:ontonotes.tsv:data/zh/ontonotes-release-5.0/ \
					 ko:corefud-ecmt.tsv:data/ko/CorefUD_Korean-ECMT/ \
					 ko:koconovel.tsv:data/ko/koconovel/corefud/ \
					 ja:ntc_1.5.tsv:data/jp/naist/NTC_1.5_corefud/\
					 ";\
	for lang_tgt_src in $$lang_tgt_srces; do \
		lang=`echo $$lang_tgt_src | cut -f 1 -d ':'`; \
		tgt=`echo $$lang_tgt_src | cut -f 2 -d ':'`;\
		src=`echo $$lang_tgt_src | cut -f 3 -d ':'`;\
		exec=scripts/corefud2gh.py;\
		filter=".*\.conllu$$";\
		if echo $$tgt $$src | grep -i ontonotes >/dev/null; then \
			exec=scripts/ontonotes2gh.py; \
			filter=".*\.coref$$";\
		fi;\
		if [ ! -e $$lang ]; then mkdir -p $$lang; fi;\
		tgt=$$lang/$$tgt;\
		if [ ! -e $$tgt ]; then \
			echo $$src '>' $$tgt 1>&2;\
			(python3 $$exec -l $$lang `find $$src | egrep $$filter` \
			> $$tgt) 2>&1 \
			| tee $$tgt.log 1>&2;\
			echo 1>&2;\
		fi;\
	done;

prep: 
	@if [ ! -e data ]; then mkdir data; fi;
	@make coref-ud ontonotes
	@cd data/ko/koconovel; make
	@cd data/jp/naist/; make

ontonotes:
	@for lang in en zh ar; do \
		if [ -e data/$$lang ]; then \
			for dir in `echo data/$$lang/ontonotes*`; do \
				if [ ! -e $$dir ]; then \
					echo please get your OntoNotes v. 5.0 copy and put all annotations for language $$lang '(and only this)' under $$dir 1>&2;\
					exit 1;\
				fi;\
			done;\
		fi;\
	done;

coref-ud:
	@for lang in ru en es; do \
		for dir in data/$$lang/CorefUD*; do \
			if [ ! -e $$dir ]; then \
				echo please deposit CorefUD data under `pwd`data/$$lang"/CorefUD*" 1>&2;\
				exit 2;\
			fi;\
		done;\
	done;\

