import sys,os,re,traceback,json
from pprint import pprint

""" read one or more *.coref files from stdin or as args, calculate salience metrics 
	Note that we do not evaluate word order nor grammatical roles
"""

class Salienizer:

	# two features: text and lcased
	lang2category2feat2patterns={
		"en": { # some texts seem to be lemmatized/stemmed, so we include the corrupt stems, too # correction: a lot of final "r"s seem to be gone
			"this N": [{ "LCASED": r"(this|these)\s.*"}], # incl. these
			"that N": [{ "LCASED": r"(that|those)\s.*"}], # incl. those
			"a N": [{ "LCASED": r"a(n|nother)?\s.*" }], # we don't check the noun in order to include nominalizations
			"quant N" : [ { "LCASED": r"(any|some|many|much|most|much|few|all|both|one|no)\s.*"}],
			"the N": [{ "LCASED": r"the\s.*" }], # we don't check the noun in order to include nominalizations
			"it": [{ "LCASED": r"(he|him|his|she|her|hers|it|its|they|them|their|theirs)$"}], # incl. her, his, him, their, them, its
			"this": [{ "LCASED": r"(this|these)$"}], # incl. these
			"that": [{ "LCASED": r"(that|those)$"}], # incl. those
			"QUANT": [ { "LCASED": r"(any|some|few|both|many|several|most|various|much|more|first|second|third|fourth|fifth|no|none|anyone|anybody|someone|somebody|anything|something|noone|nobody|none|nothing|everyone|everything|everybody)$"}],
			"(other) PRON": [{"TEXT":r"I$"}, {"LCASED":r"(me|my|mine|you|your|yours|thou|thy|thine|we|us|our|ours|another|other|others|such|wh[^\s]*|.*self|.*selves)$"}],
			"name": [{"TEXT":r"[A-Z].*"}], # anything containing an upper case letter not included in the other categories
			"(other) N": [{"LCASED": r"(i|you|he|it|she|thei|ou|such|my|your|his|her|its|our|their|whose|.*'s|every|each|one|two|three|four|five|six|seven|eight|nine|ten|[0-9]|[0-9]th)\s.*"}],
			"N": [{"LCASED":r"[^\s]+s(\s.*)?$"}], # bare plurals
			"N?": [{"LCASED":r"^[^\s]+$"}] # incl. bare nouns
		},
		"zh": { # tbc by a language expert
			"tā": [{ "TEXT": r"(他|她|它)"}], # 3rd person pronouns
			"zhè": [{"TEXT": r"这个|这$|这些$"}], # dem pron		
			"nà": [{"TEXT": r"那个|那$|那些$"}], # dem pron
			"ADV": [{"TEXT": r"这儿|这里|那儿|那里|这边|那边"}], # here/there, this side, that side
			"zhè N": [{ "TEXT": r"这.*"}], # dem N
			"nà N": [{"TEXT": r"那.*"}], # dem N
			"a N": [{ "TEXT": r"一.*" }], # we don't check the noun in order to include nominalizations
			"persons": [{"TEXT": r"名|位"}], # cf. https://en.wikipedia.org/wiki/List_of_Chinese_classifiers 
			"N?" : [ { "TEXT": r".*"}],
		}
		# as for Arabic, we unfortunately don't know for sure which patterns to expect, and mining them from the OntoNotes lemmatized corpus failed because of alignment/normalization errors
	}

	ref2sentence2text=None
	category2feat2patterns={}

	def __init__(self, language=None, category2feat2patterns=None):
		self.ref2sentence2text={}
		if category2feat2patterns!=None:
			self.category2feat2patterns=category2feat2patterns
		elif language!=None and language in self.lang2category2feat2patterns:
			self.category2feat2patterns=self.lang2category2feat2patterns[language]
		if self.category2feat2patterns in [None,{}]:
			if not language in self.lang2category2feat2patterns:
				raise Exception(f"unsupported language {language}, please choose one of {list(self.lang2category2feat2patterns.keys())}  or provide an explicit value for category2feat2patterns")
			else:
				raise Exception("please specify a supported language code or provide an explicit value for category2feat2patterns")


	def add_text(self, text):
		""" we add text as a stream, string or file.
			a sentence is a single line in the *.coref file (if it does not just contain markup only) 
			IDs are unique within a text only 
			note that this will fail for recursive refexpes, e.g., [[Hong Kong] Disneyland]
		"""

		if isinstance(text,str):
			if os.path.exists(text):
				with open(text,"rt",errors="ignore") as stream:
					self.add_text(stream)
			else:
				self.add_text(str.split("\n"))

		else: # stream or list of lines

			text_id=""
			sentence=0
			for line in text:
				line=line.strip()
				if "DOCNO=" in line:
					text_id=re.sub(".*DOCNO=.([^'"'"'"]+).*",r"\1",line).strip()
					sentence=0
				text=re.sub(r"r<[^>]*>","",line).strip()
				if text!="":
					sentence+=1
					if "<" in text:
						for chunk in text.split("<"):
							if chunk.startswith("COREF"):
								refexp=chunk.split(">")[1]
								id=re.sub(r'.*ID="([^"]+)".*',r'\1',chunk)
								id=text_id+"_"+id
								if not id in self.ref2sentence2text: 
									self.ref2sentence2text[id]={sentence:refexp}
								elif not sentence in self.ref2sentence2text[id]: 
									self.ref2sentence2text[id][sentence]=refexp
								elif len(refexp) > len(self.ref2sentence2text[id][sentence]): 
									self.ref2sentence2text[id][sentence]=refexp
									# we keep the longest referent, only

	def analyze(self, debug=False):
		""" note that we only use COREF files, no grammatical features are extracted, no verbs, etc.
			extraction is rule-based in original case and lower case mode """

		ref2sentence2text=self.ref2sentence2text
		if debug: pprint(ref2sentence2text)
		for ref in ref2sentence2text:
			for sentence,text in ref2sentence2text[ref].items():
				text=" ".join(text.split()).strip()
				word={"TEXT":text,"LCASED":text.lower()}

				# first iteration: check whether it matches the beginning
				for cand in self.category2feat2patterns:
					for feat2pattern in self.category2feat2patterns[cand]:
						match=True
						for f,p in feat2pattern.items():
							p=r"^"+p
							if p.startswith("^^"): p=p[1:]
							
							if debug and f in word: print(re.match(p,word[f]),word[f],p)
							
							if not f in word or not re.match(p,word[f]):
								match=False
								break
						if match:
							word["CAT"]=cand
							break
					if "CAT" in word: break

				# second iteration: check whether it matches anywhere in string
				if not "CAT" in word:
					for cand in self.category2feat2patterns:
						for feat2pattern in self.category2feat2patterns[cand]:
							match=True
							for f,p in feat2pattern.items():
								if not "^" in p:
									p=r"(.*\s)"+p
								if not f in word or not re.match(p,word[f]):
									match=False
									break
							if match:
								word["CAT"]=cand
								break

				if not "CAT" in word: word["CAT"]="_"

				vals=[]
				COLS=["CAT","TEXT","UPOS","XPOS","FEATS","EDGE","DEPTH"]
				for col in COLS:
					if not col in word:
						word[col]="_"
					vals.append(word[col])
							
				# referential distance and topic persistence
				rd=None
				tp=0
				tp_20=0
				tp_1=0
				ri_20=0 # ~ Chafe's referential importance, modelled here as frequency in the preceding discourse, closer to Chafe's original would be ri_20 + tp_20 
				for s in self.ref2sentence2text[ref]:
								if s < sentence:
									if rd==None:
										rd=sentence-s
									else:
										rd=min(rd,sentence-s)
								if s-20>=sentence and s!=sentence:
									ri_20+=1
								if s > sentence:
									tp+=1
									if s-sentence <= 20:
										tp_20+=1
									if s-sentence==1:
										tp_1=1

				vals+=[rd,tp_1,tp_20,tp,ri_20]

				# word order features
				vals.append("_") # WORD_RELATIVE
				vals.append("_") # WORD_PERIPHERY
				vals.append("_") # WORD_VERB

				hsal_RD=0
				hsal_lin=0
				try:
					hsal_RD=1/rd
					hsal_lin=max(20-rd,0) / 20
				except Exception:
					pass

				ssal_TP_1=0
				ssal_TP=0
				ssal_TP_20=0
				ssal_lin_20=0
				hsal_RI_20=0
				ssal_RI_40=0
				ssal_FF_20=0

				try:
					ssal_TP=1-1/(1+tp)
					ssal_TP_1=1-1/(1+tp_1)
					ssal_TP_20=1-1/(1+tp_20)
					ssal_lin_20=tp_20/20
					hsal_RI_20=ri_20/20
					ssal_RI_40=(ssal_lin_20+hsal_RI_20)/2
					ssal_FF_20=ssal_lin_20 - hsal_RI_20 

				except Exception:
					pass

				vals+=[hsal_RD,ssal_TP_1,ssal_TP_20,ssal_TP,hsal_lin,ssal_lin_20,hsal_RI_20,ssal_RI_40,ssal_FF_20]

				print("\t".join([str(v) for v in vals]))
			print()

if __name__ == "__main__":

	import argparse
	args=argparse.ArgumentParser(description="""calculate salience scores, using default configurations or a JSON file with category2feat2patterns""")
	args.add_argument("files", type=str, nargs="*", help="ontonotes coref files", default=[])
	args.add_argument("-l", "--language", type=str, nargs="?", help="language, defaults to en", default="en")
	args.add_argument("-debug", action="store_true")
	args.add_argument("-c","--config", type=str, nargs="?", help="JSON configuration file with gundel category -> [ (feature, pattern)* ]; note: this overrides defaults for language as defined from -l", default=None)
	args=args.parse_args()

	files=args.files
	DEBUG=args.debug
	lang=args.language
	config=None
	if args.config!=None:
		with open(args.config,"rt",errors="ignore") as input:
			config=json.load(input)

	print("FILES:",files)

	if len(files)==0:
		sys.stderr.write("reading from stdin\n")
		files=[sys.stdin]

	sys.stderr.flush()
	me=Salienizer(language=lang, category2feat2patterns=config)

	for file in files:
		me.add_text(file)

	me.analyze(debug=DEBUG)