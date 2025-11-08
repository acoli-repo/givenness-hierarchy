all: prep

prep: 
	@if [ ! -e data ]; then mkdir data; fi;
	@make coref-ud ontonotes

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
