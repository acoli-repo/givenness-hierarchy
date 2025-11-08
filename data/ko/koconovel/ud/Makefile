SHELL=bash

all: mrg
	for file in `find | egrep '\.mrg\.conll$$'`; do \
		tgt=../corefud/`echo $$file | sed s/'\.mrg\.conll$$'//`-corefud.conllu;\
		if [ ! -e $$tgt ]; then \
			if [ ! -e `dirname $$tgt` ]; then mkdir -p `dirname $$tgt`; fi;\
			echo $$file '>' $$tgt 1>&2;\
			cat $$file \
			| cut -f 4,12- \
			| sed s/'.*\t.*'/'&\t&'/g \
			| cut -f 3-14 \
			| perl -pe 's/^[?]\t[?]\t(.*\t([^\t]+)\t[^\t]*)$$/?\t\2\t\1/g;' \
			| cut -f 1-10,12 \
			| perl -pe 's/\t([\(\)0-9]+)$$/|Entity=\1/g;' \
			 	   	-e 's/\t[_?]\|/\t/g;' \
			| cut -f 1-10 \
			| grep -P '^$$|.*[0-9]'\
			> $$tgt;\
		fi;\
	done;

mrg: tools/udpipe tools/udpipe/models/ko tools/conll-merge
	@model=`find tools/udpipe/models/ko | grep -m 1 'udpipe$$'`; \
	 if [ ! -e $$model ]; then \
	 	echo error: did not find a UDpipe model under `pwd`/tools/udpipe/models/ko 1>&2; \
	 else \
	 	echo using $$model 1>&2;\
	 fi;\
	 for src in `find ../data/conll/omniscent_separate | grep '\.conll$$'`; do \
	 	tgtdir=`basename $$(dirname $$src)`;\
		tgt=$$tgtdir/`basename $$src`u;\
		echo -n $$src 1>&2;\
		if [ ! -e $$tgt ]; then \
			if [ ! -e $$tgtdir ]; then mkdir -p $$tgtdir; fi;\
			echo -n ' >' $$tgt 1>&2;\
			cat $$src \
			| sed s/'  *'/'\t'/g \
			| cut -f 4 \
			| perl -pe 's/([^\s])\n/\1 /g;'\
			| tools/udpipe/src/udpipe --input=conll --tokenize --tag --parse --output=conllu $$model 2>/dev/null \
			> $$tgt;\
		fi;\
		\
		mrg=$$tgtdir/`basename $$src | sed s/'\.conll$$'//`.mrg.conll;\
		if [ ! -e $$mrg ]; then \
			echo -n ' >' $$mrg 1>&2;\
			cat $$src \
			| sed s/'  *'/'\t'/g \
			| python3 tools/conll-merge/experimental/align.py 50 --=3 $$tgt=1 \
			> $$mrg;\
		fi;\
		echo 1>&2;\
	 done

tools/conll-merge:
	@if [ ! -e tools/conll-merge ]; then echo "please install (or symlink) CoNLL-Merge under "`pwd`/tools/conll-merge; exit 1; fi

tools/udpipe: 
	@if [ ! -e tools/udpipe ]; then echo "please install (or symlink) UDpipe v.1 under "`pwd`/tools/udpipe; exit 1; fi

tools/udpipe/models/ko: 
	@if [ ! -e tools/udpipe/models/ko ]; then echo "please install (or symlink) a Korean UDpipe v.1 model under "`pwd`/tools/udpipe/models/ko; exit 2; fi

