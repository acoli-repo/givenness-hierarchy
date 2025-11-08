import sys,os,re,traceback,json
from pprint import pprint

""" read one or more corefud files from stdin or as args, calculate salience metrics """

class Salienizer:

	ref2sentence2id2feats=None 		# features for referents
	sentence2verb_id2feats=None 	# because position relative to finite verbs may be important
	sentence2nomid2feats=None 		# nominals identified by UD syntax, this is to account for annotation schemes with annotations for actual anaphors and their antecedents, only; note that we include expletives
	sentence=None
	FIELDS="ID FORM LEMMA UPOS XPOS FEATS HEAD EDGE DEPS MISC".split()

	lang2category2feat2patterns={
		"en": {
			"the N": [{ "LEMMAS": r"^(.*\s)?the\s.*" }], # we don't check the noun in order to include nominalizations
			"a N": [{ "LEMMAS": r"^(.*\s)?a(n|nother)?\s.*" }], # we don't check the noun in order to include nominalizations
			"this N": [{ "LEMMAS": r"^(.*\s)?(this)\s.*", "UPOS": "NOUN" }], # incl. these
			"that N": [{ "LEMMAS": r"^(.*\s)?(that)\s.*", "UPOS": "NOUN" }], # incl. those
			"quant N" : [ { "LEMMAS": r"^(any|some|many|much|most|much|few|all|both|one|no)", "UPOS":"NOUN" },
						  { "UPOSES": r".*NUM.*NOUN"}],
			"N": [{"UPOS":"NOUN", "UPOSES":r"[^D]"}, {"UPOS":"NOUN", "UPOSES":r"[^T]"}, {"UPOS":"NOUN", "UPOSES":r"[^E]"}], # nouns without determiners (heuristically)
			"(other) N": [{ "UPOS": "NOUN"} ], # incl. bare plurals
			"name": [{ "UPOS": "PROPN" }, 
				     {"XPOS": r"NNP.*"},
				     {"LEMMA": r"^[A-Z].*"}],
			"it": [{ "UPOS": "PRON", "LEMMA": r"(he|she|it|they)"}], # incl. her, his, him, their, them, its
			"this": [{ "UPOS":"PRON", "LEMMA": "this"}], # incl. these
			"that": [{ "UPOS":"PRON", "LEMMA": "that"}], # incl. those
			"QUANT": [ { "LEMMA": r"^(any|some|few|both|many|several|most|various|much|more|first|second|third|fourth|fifth|no|none)"},
					   { "UPOS" : "NUM"}],
			"(other) PRON": [ # other pronouns, i.e., non-3rd person personal pronouns
				{ "UPOS":"PRON"},
				{ "LEMMA" : r"^(another|other|such)"}
				] 		
			},
			"N?": [{"UPOSES": r".*NOUN.*"}],
			"name?": [{"UPOSES": r".*PROPN.*"}, {"XPOSES": r".*NNP.*" }, {"LEMMAS": r".*[A-Z].*"} ],
			"PRON?": [{"UPOSES": r".*PRON.*"}],
		"es": {
			"Ø": [ { "LEMMA": "_", "UPOS":"PRON", "MISC": r".*Entity=" }], # zero, marked by ID.1 with the ID of the preceding word, only annotated in DEPS column !
			"él": [ { "UPOS": "PRON", "LEMMA":"él" }], # he (also other genders)
			"éste": [ {"UPOS":"PRON", "LEMMA": "este"}, {"UPOS":"PRON", "LEMMA": "éste"}], # this (LEMMA accents confirmed)
			"ése": [ { "UPOS":"PRON", "LEMMA": "ese"}], # that, medial (LEMMA accent confirmed)
			"aquél": [ {"UPOS":"PRON", "LEMMA": "aquel"}], # that, distal (LEMMA accent confirmed!)
			"other DEM": [{"UPOS":"PRON", "LEMMA": "mismo|tal|tanto"}], # other pronouns marked as demonstrative in UD
			"este N": [{"LEMMAS": r"^(.*\s)?este\s.*"}], # this N
			"ese N": [{"LEMMAS": r"^(.*\s)?ese\s.*"}], # that N, medial
			"aquel N": [{"LEMMAS": r"^(.*\s)?aquel\s.*"}], # that N, distal
			"other DEM N": [{"UPOS":"NOUN", "LEMMAS": r"^(.*\s)?(mismo|tal|tanto)\s.*"}], # other pronouns marked as demonstrative in UD
			"el N": [
				{"LEMMAS": r"^(.*\s)?el\s.*"},
				{"LEMMAS": r"^(.*\s)?els\s.*"},
				{"LEMMAS": r"^(.*\s)?Els\s.*"},
				{"LEMMAS": r"^(.*\s)?o\s.*"}], # the N
			"name": [{ "UPOS": "PROPN" }],
			"N": [{"UPOS":"NOUN", "UPOSES":r"[^D]"}, {"UPOS":"NOUN", "UPOSES":r"[^T]"}, {"UPOS":"NOUN", "UPOSES":r"[^E]"}], # nouns without determiners (heuristically)
			"un N": [{ "LEMMAS": r"^(.*\s)?uno\s.*" }], # a N, lemmatization checked
			"(other) N": [{ "UPOS": "NOUN"} ], # incl. bare plurals
			"(other) PRON": [ { "UPOS":"PRON"} ],  		
			"N?": [{"UPOSES": r".*NOUN.*"}],
			"name?": [{"UPOSES": r".*PROPN.*"} ],
			"PRON?": [{"UPOSES": r".*PRON.*"}],
		},
		"ru": {
			# "Ø": [] # no annotations
			"on": [ { "UPOS": "PRON", "LEMMA":"он" }, 
			        { "UPOS": "PRON", "LEMMA":"оно" },
			        { "UPOS": "PRON", "LEMMA":"они" },
			        { "UPOS": "PRON", "LEMMA":"она" }], # he (also other genders)
			"èto": [ {"UPOS":"PRON", "LEMMA": "это"}], # this 
			"to": [ { "UPOS":"PRON", "LEMMA": "то"}], # that
			"èto N": [ {"LEMMAS": r"^(.*\s)?этот\s.*"}], #
			"to N": [{"LEMMAS": r"^(.*\s)?тот\s.*"}], # 
			"N": [{"UPOS":"NOUN", "UPOSES":r"[^D]"}, {"UPOS":"NOUN", "UPOSES":r"[^T]"}, {"UPOS":"NOUN", "UPOSES":r"[^E]"}], # nouns without determiners (heuristically)
			"other DEM N": [{"UPOS":"NOUN", "LEMMAS": r"^(.*\s)?(сей|такой)\s.*"}], # other determiners marked as demonstrative in UD			
			"name": [{ "UPOS": "PROPN" }],
			"(other) N": [{ "UPOS": "NOUN"} ], 
			"(other) PRON": [ { "UPOS":"PRON"} ],  		
			"N?": [{"UPOSES": r".*NOUN.*"}],
			"name?": [{"UPOSES": r".*PROPN.*"} ],
			"PRON?": [{"UPOSES": r".*PRON.*"}]
	}}

	def __init__(self, language=None, category2feat2patterns=None):
		self.ref2sentence2id2feats={}
		self.sentence=0
		self.sentence2verbid2feats={}
		if category2feat2patterns==None and language in self.lang2category2feat2patterns:
			category2feat2patterns=self.lang2category2feat2patterns[language]
		self.category2feat2patterns=category2feat2patterns
		self.sentence2nomid2feats={}


	def add_sentence(self, array_of_arrays):
		""" array_of_array: array of rows, each row an array of fields 
			note that we expect data only, no comments nor empty lines 
			over COREF UD data, it performs head reduction and applies POS and dep filters to weed out non-referring expressions """
		sentence=self.sentence
		ref2sentence2id2feats=self.ref2sentence2id2feats
		sentence2verbid2feats=self.sentence2verbid2feats
		
		if len(array_of_arrays)>0:
			sentence+=1
			refs=[]

			# convert all rows to dicts
			buffer={ row[0] : dict(zip(self.FIELDS,row)) for row in array_of_arrays }

			# extract nominals from UD annotation
			self.sentence2nomid2feats[sentence]={}
			for word in buffer.values():
				if 	word["EDGE"].split(":")[0] in ["nsubj","obj","iobj","obl","vocative","expl","dislocated","nmod"] or \
					( word["EDGE"].split(":")[0] in ["root","csubj","ccomp","xcomp","advcl","acl","conj"] and \
					  word["UPOS"] in ["NOUN","PROPN","PRON"] ): # nominal sentential heads
					self.sentence2nomid2feats[sentence][word["ID"]]={ k:v for k,v in word.items() }
			#pprint(self.sentence2nomid2feats[sentence].items())

			# preprocessing: 
			for id,word in buffer.items():

				# (0) attach zero pronouns (Spanish)
				if word["HEAD"]=="_" and word["EDGE"]=="_" and ":" in word["DEPS"]:
					buffer[id]["HEAD"]=word["DEPS"].split(":")[0]
					buffer[id]["EDGE"]=re.sub(r"[^a-z].*","",word["DEPS"].split(":")[1])
					word["HEAD"]=word["DEPS"].split(":")[0]
					word["EDGE"]=re.sub(r"[^a-z].*","",word["DEPS"].split(":")[1])

				# (a) add shallow label (i.e. lemmas of head and all direct dependents)
				lemmas=[]
				words=[]
				uposes=[]
				xposes=[]
				for dep in buffer.values():
					if word["ID"] in [dep["ID"],dep["HEAD"]]:
						lemmas.append(dep["LEMMA"])
						words.append(dep["FORM"])
						uposes.append(dep["UPOS"])
						xposes.append(dep["XPOS"])
				buffer[id]["LEMMAS"]=" ".join(lemmas)
				buffer[id]["UPOSES"]=" ".join(uposes)
				buffer[id]["XPOSES"]=" ".join(xposes)

				# (b) extract UD paths to root / embedding depth
				heads=[]
				head=word["ID"]
				while head in buffer and not head in heads:
					heads.append(head)
					head=buffer[head]["HEAD"]
				buffer[id]["HEADS"]=heads
				buffer[id]["DEPTH"]=len(heads)-1

			# (c) extract full text for all potentially finite verbs and root
			for id,word in buffer.items():
				if word["UPOS"] in ["VERB","AUX"] or word["EDGE"].split(":")[0] in ["cop","xcomp","ccomp","csubj","aux","root"]:
					buffer[id]["PRED"]=True
				forms=[]
				for dep in buffer.values():
					if word["ID"] in dep["HEADS"]:
						forms.append(dep["FORM"])
				buffer[id]["TEXT"]=" ".join(forms)

			# extract referents from coref annotation
			for word in buffer.values():
				if "MISC" in word:
					misc=word["MISC"].split("|")
					misc={ x.split("=")[0]:x.split("=")[1] for x in misc if "=" in x}
					if "Entity" in misc:
						ref=re.sub(r"[^a-zA-Z0-9]+","",misc["Entity"].split(")")[0].split("-")[0])
						if not ref in refs: refs.append(ref)
						if not ref in ref2sentence2id2feats: ref2sentence2id2feats[ref]={}
						if not sentence in ref2sentence2id2feats[ref]: ref2sentence2id2feats[ref][sentence]={}
						ref2sentence2id2feats[ref][sentence][word["ID"]]={ k:v for k,v in word.items() if not k in ["ID","LEMMA","FORM","MISC","DEPS", "HEADS","PRED"] and not v in ["_","","-"] }
						
						if self.category2feat2patterns!=None:
							for category,feat2patterns in self.category2feat2patterns.items():
								for feat2pattern in feat2patterns:
									match=True
									for feat,pattern in feat2pattern.items():
										if not feat in word or not re.match(pattern,word[feat]):
											match=False
											break
									if match:
										ref2sentence2id2feats[ref][sentence][word["ID"]]["CAT"]=category
										break
								if "CAT" in ref2sentence2id2feats[ref][sentence][word["ID"]]:
									break
						if not "CAT" in ref2sentence2id2feats[ref][sentence][word["ID"]] and \
							   "PRED" in ref2sentence2id2feats[ref][sentence][word["ID"]] and \
							   ref2sentence2id2feats[ref][sentence][word["ID"]]["PRED"]==True:
							   ref2sentence2id2feats[ref][sentence][word["ID"]]["CAT"]="PRED"

			# pruning
			for ref in refs:
				removables=[]
				for id in ref2sentence2id2feats[ref][sentence]:
					# remove words whose head is annotated for the same entity (we enforce head-based annotation)
					if ref2sentence2id2feats[ref][sentence][id]["HEAD"] in ref2sentence2id2feats[ref][sentence]:
						removables.append(id)
					# implement a POS filter
					elif not ref2sentence2id2feats[ref][sentence][id]["UPOS"] in ["NOUN", "PROPN", "PRON", "VERB", "ADJ"]:
						removables.append(id)
					# implement a dependency filter
					elif ref2sentence2id2feats[ref][sentence][id]["EDGE"] in ["compound","flat","mwe","expl"]:
						removables.append(id)
					# remove HEAD
					ref2sentence2id2feats[ref][sentence][id].pop("HEAD")
				
				for id in removables:
					ref2sentence2id2feats[ref][sentence].pop(id)
					if len(ref2sentence2id2feats[ref][sentence])==0: ref2sentence2id2feats[ref].pop(sentence)
					if len(ref2sentence2id2feats[ref])==0: ref2sentence2id2feats.pop(ref)

			# extract verbs
			sentence2verbid2feats[sentence]={}
			for word in buffer.values():
				if "PRED" in word and word["PRED"]==True:
					sentence2verbid2feats[sentence][word["ID"]]= {k:v for k,v in word.items() if k in ["DEPTH","TEXT","FEATS","EDGE", "LEMMA","UPOS","XPOS"] }

		self.sentence=sentence
		self.ref2sentence2id2feats=ref2sentence2id2feats
		self.sentence2verbid2feats=sentence2verbid2feats

	def analyze(self):
		""" note that we also exploit UD to retrieve potentially referring expressions (i.e., all nominals and pronouns)
			this is because the coreference annotation may have gaps """

		sentence2ref2feats={}

		for sentence,verbid2feats in self.sentence2verbid2feats.items():
			text=""
			for feats in verbid2feats.values():
				if "TEXT" in feats and len(feats["TEXT"]) > len(text): text=feats["TEXT"]
			print("# "+text)
			pos2entry={}
			for ref,sentence2id2feats in self.ref2sentence2id2feats.items():
				if sentence in sentence2id2feats:
					id=None
					for cand in sentence2id2feats[sentence]:
						if id==None: 
							id=cand
						elif sentence2id2feats[sentence][cand]["UPOS"] in ["PROPN","NOUN"] and not sentence2id2feats[sentence][id]["UPOS"] in ["PROPN","NOUN"]:
							id=cand
						elif len(sentence2id2feats[sentence][cand]["UPOSES"]) > len(sentence2id2feats[sentence][id]["UPOSES"]):
							id=cand
						elif len(sentence2id2feats[sentence][cand]["UPOSES"]) == len(sentence2id2feats[sentence][id]["UPOSES"]):
							if not "LEMMAS" in sentence2id2feats[sentence][id] or "LEMMAS" in sentence2id2feats[sentence][cand] and len(sentence2id2feats[sentence][cand]["LEMMAS"]) > len(sentence2id2feats[sentence][id]["LEMMAS"]):
								id=cand

					if id!=None:
						# extracted features
						pos=int(re.sub(r"[^0-9]+"," ",id).strip().split()[0])
						if not pos in pos2entry:
							vals=[]
							for col in ["CAT", "TEXT","UPOS","XPOS","FEATS","EDGE","DEPTH"]:
								if col in sentence2id2feats[sentence][id]:
									vals.append(sentence2id2feats[sentence][id][col])
								else:
									vals.append("_")
							
							# referential distance and topic persistence
							rd=None
							tp=0
							tp_20=0
							tp_1=0
							ri_20=0 # ~ Chafe's referential importance, modelled here as frequency in the preceding discourse, closer to Chafe's original would be ri_20 + tp_20 
							for s in self.ref2sentence2id2feats[ref]:
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

							if "CAT" in sentence2id2feats[sentence][id] or tp>0 or rd!=None:
								pos2entry[pos]=vals
								# in en/CorefUD/GUM, a lot of adjectives were annotated as entities, but without links, these will be filtered out

			for verbid,verb in verbid2feats.items():
				pos=int(re.sub(r"[^0-9]+"," ",verbid).strip().split()[0])
				if not pos in pos2entry:
					vals=["PRED"] # ~ CAT
					for col in ["LEMMA","UPOS","XPOS","FEATS","EDGE","DEPTH","_","_","_","_","_"]:
						if col in verb:
							vals.append(verb[col])
						else:
							vals.append("_")
					pos2entry[pos]=vals
			
			# addenda: other nominals, incl. expletives (these are important for word order)
			for nomid,nom in self.sentence2nomid2feats[sentence].items():
				pos=int(re.sub(r"[^0-9]+"," ",nomid).strip().split()[0])
				if not pos in pos2entry:
					vals=["_"]
					for col in ["LEMMA","UPOS","XPOS","FEATS","EDGE","DEPTH","_","_","_","_","_"]:
						if col in nom:
							vals.append(nom[col])
						else:
							vals.append("_")
					pos2entry[pos]=vals

			# word order features
			entries = [ entry for _,entry in sorted(pos2entry.items()) ]
			if len(entries)>0:

				# relative word order, only non-predicates
				non_preds=len([ e for e in entries if e[0]!="PRED"])
				prev_es=0
				for e in range(len(entries)):
					if non_preds<=1:
						entries[e].append("_")
					elif entries[e][0]!="PRED":
						entries[e].append(prev_es/(non_preds-1))
						prev_es+=1
					else:
						entries[e].append("_")

				# mark initial element
				entries[0].append("initial")
				if len(entries)>1:
					entries[-1].append("final")
				for x in range(1,len(entries)-1):
					entries[x].append("medial")

				# mark pre-verbal elements
				if "VERB" in str(entries) or "AUX" in str(entries):
					prev_pred=False
					for e in range(len(entries)):
						if entries[e][0]=="PRED": 
							prev_pred=True
							entries[e].append("verbal")
						elif prev_pred:
							entries[e].append("postverbal")
						else:
							entries[e].append("preverbal")
				else:
					for e in range(len(entries)):
						entries[e].append("_")

			# salience metrics
			for e in range(len(entries)):
				fields=dict(zip(["CAT","TEXT","UPOS","XPOS","FEATS","EDGE","DEPTH","RD","TP_1","TP_20","TP","RI_20", "WO_REL","WO_PERIPHERY","WO_VERB"],entries[e]))

				hsal_RD=0
				hsal_lin=0
				try:
					hsal_RD=1/float(fields["RD"])
					hsal_lin=max(20-float(fields["RD"]),0) / 20
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
					ssal_TP=1-1/(1+float(fields["TP"]))
					ssal_TP_1=1-1/(1+float(fields["TP_1"]))
					ssal_TP_20=1-1/(1+float(fields["TP_20"]))
					ssal_lin_20=float(fields["TP_20"])/20
					hsal_RI_20=float(fields["RI_20"])/20
					ssal_RI_40=(ssal_lin_20+hsal_RI_20)/2
					ssal_FF_20=ssal_lin_20 - hsal_RI_20 

				except Exception:
					pass

				entries[e]+=[hsal_RD,ssal_TP_1,ssal_TP_20,ssal_TP,hsal_lin,ssal_lin_20,hsal_RI_20,ssal_RI_40,ssal_FF_20]

			for entry in entries:
				print("\t".join([str(v) for v in entry]))
			print()

lang="en"
files=sys.argv[1:]

if not os.path.exists(sys.argv[1]):
	lang=sys.argv[1]
	files=sys.argv[2:]

if len(files)==0:
	sys.stderr.write("reading from stdin\n")
	files=[sys.stdin]

sys.stderr.flush()
for file in files:
	if isinstance(file,str):
		file=open(file,"rt",errors="ignore")

	me=Salienizer(language=lang)
	buffer=[]

	for line in file:
		line=line.strip()
		if line=="" and len(buffer)>0:
			me.add_sentence(buffer)
			buffer=[]
		if line.startswith("#"):
			continue
		lastline=line
		fields=line.split("\t")
		if len(fields)>9:
			buffer.append(fields)
	if(len(buffer)>0):
		me.add_sentence(buffer)
	file.close()

	me.analyze()
#	pprint(me.get_grid())