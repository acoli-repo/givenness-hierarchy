all: NTC_1.5
	@for file in NTC_1.5/dat/num/ipa/*.dat; do \
		tgt=NTC_1.5_corefud/`basename $$file | sed s/'\.dat$$'//`.corefud.conllu;\
		if [ ! -e $$tgt ]; then \
			if [ ! -e `dirname $$tgt` ]; then mkdir -p `dirname $$tgt`; fi;\
			echo $$file '>' $$tgt 1>&2;\
			(python3 ipa2conll.py $$file ja_core_news_sm \
			 > $$tgt) 2>&1 \
			| tee $$tgt.log 1>&2;\
		fi;\
	done;

NTC_1.5:
	if [ ! -e NTC_1.5 ]; then \
		tar -xvf NTC_1.5.tgz;\
	fi;