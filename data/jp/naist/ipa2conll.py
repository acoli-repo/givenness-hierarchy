import sys,re,os,argparse
from pprint import pprint
import spacy

""" read IPA file, extract coref annotation (direct annotations, not spans!) 
	note that we loose sentence boundaries and annotations => to be combined with CoNLL-U annotations
	using these, then: pron => stays, DETERMINER => head, other ID stays

	Note, with the current configuration, there are definitely errors in the coreference chains, for some elements it is to greedy 
	(e.g., 
		村山	 富市	 首相 "Prime Minister Tomiichi Murayama"	 (e1)
		グロズヌイ	"Grozny" (e1) 
	)
		other sub-chains should be merged.

	I guess they used the same IDs over multiple texts
	This data probably gives a bit of a biased view.
"""

args=argparse.ArgumentParser(description="reading NTC IPA files and produce CorefUD-comparable data")
args.add_argument("files", type=str, nargs="+", help="one or more NTC IPA files, expect EUCJP encoding (note: converted to UTF-8)")
args.add_argument("spacy_model", type=str, help="spacy model; right now, we only support native spacy models, no UDPipe, cf. https://spacy.io/models/ + BCP47 language tag, e.g., https://spacy.io/models/ko for Korean. To install a SpaCy model, you can use `python -m spacy download $MODEL`")
sentence_separator=r".*[!?.！？。！？。؟!]['\"»“】］\]）)]*$"
args.add_argument("-s", "--sentence_separator", type=str, help="regular expression to be used for sentence splitting. Note that this is applied to individual, whitespace-separated tokens. Note that we keep all matches, but insert a sentence break right after each match, defaults to {sentence_separator}", default=sentence_separator)
args=args.parse_args()

parser=spacy.load(args.spacy_model)

# keep tokenization
tokenizer=spacy.tokenizer.Tokenizer(parser.vocab, token_match=re.compile(r'\S+').match)

for file in args.files:
	# direkte extraktion, CoNLL-U parse, regelgeleitete projektion auf die nächsthöhere phrase
	print(f"# newdoc id: {file}")
	print()
	with open(file,"rt", encoding="EUCJP", errors="ignore") as input:
		sentences=[ { "words": [], "idxes":[], "coref": []}]
		for line in input:
			if "\t" in line:
				line=line.strip()
				fields=line.split("\t")
				word=fields[2]
				coref=fields[7]
				sentences[-1]["idxes"].append(len((" ".join(sentences[-1]["words"])+" ").lstrip()))
				sentences[-1]["words"].append(word.strip())
				sentences[-1]["coref"].append(coref)

				if re.match(args.sentence_separator,word):
					sentences[-1]["parsed"]=parser(" ".join(sentences[-1]["words"]))
					sentences.append({"words":[],"idxes":[], "coref":[]})

		if len(sentences[-1]["words"])==0:
			sentences=sentences[:-1]
		else:
			sentences[-1]["parsed"]=parser(" ".join(sentences[-1]["words"]))

	merged=[[]]
	# list of sentences
	# with every sentence a list of 10 CoNLL-U columns plus coref annotations

	for sentence in sentences:

		words=sentence["words"]
		coref=sentence["coref"]
		idxes=sentence["idxes"]

		annos=[] # can be more than one token, we later move coref annotation to its head
		for tok in sentence["parsed"]:
			if tok.idx in idxes:
				annos.append([tok])
			else:
				annos[-1].append(tok)

		tok_corefs=[]
		for w,a,c in zip(words,annos,coref):
			if len(a)==1:
				merged[-1].append([str(a[0].i+1), a[0].text, a[0].lemma_, a[0].pos_, "_", "_", str(a[0].head.i+1), a[0].dep_,"_","_",c])
			elif c=="_":
				for tok in a:
					merged[-1].append([str(tok.i+1), tok.text, a[0].lemma_, tok.pos_, "_", "_", str(tok.head.i+1), tok.dep_,"_","_","_"])
			else:
				dep2head={ tok.i+1 : tok.head.i+1 for tok in a }
				for tok in a:
					if tok.head.i == tok.i or not tok.head.i+1 in dep2head: 
						merged[-1].append([str(tok.i+1), tok.text, a[0].lemma_, tok.pos_, "_", "_", str(tok.head.i+1), tok.dep_,"_","_",c])
						c="_" # in case there are multiple "heads"
					else:
						merged[-1].append([str(tok.i+1), tok.text, a[0].lemma_, tok.pos_, "_", "_", str(tok.head.i+1), tok.dep_,"_","_","_"])
		
		if len(merged[-1])>0:
			merged.append([])

	# adjust merged to conform with UD specs
	for snr,sentence in enumerate(merged):
		for wnr,row in enumerate(sentence):
			if row[0]==row[6]:
				merged[snr][wnr][6]="0" # spaCy uses a cycle for roots
				merged[snr][wnr][7]=merged[snr][wnr][7].lower() # spaCy spells ROOT in upper case

	# propagate coref annotations from DETERMINER to head, mark every feature x as DET_x
	for snr,sentence in enumerate(merged):
		for wnr,row in enumerate(sentence):
			coref={ feat.split("=")[0] : "=".join(feat.split("=")[1:]).strip('"') for feat in row[10].split() if "=" in feat}
			if "refexp_type" in  coref and coref["refexp_type"]=="DETERMINER":
				if row[6]!="0" and row[6]!=row[0]: # must not be root
					hnr=int(row[6])-1 # head row number
					merged[snr][hnr][10]=merged[snr][hnr][10].strip("_")
					merged[snr][hnr][10]+=" "+ " ".join( [ "DET_"+feat for feat in row[10].split() ] )
					merged[snr][hnr][10]=merged[snr][hnr][10].strip()
					merged[snr][wnr][10]=f"comment=COREF->{hnr+1}"

	# create ID clusters
	eqs=[]
	zero_ids=[]
	for sentence in merged:
		for row in sentence:
			coref={ feat.split("=")[0] : "=".join(feat.split("=")[1:]).strip('"') for feat in row[10].split() if "=" in feat}
			ids=[]
			if "ana_id" in coref and (not "ana_type" in coref or coref["ana_type"]=="DIRECT"):
				ids.append(coref["ana_id"])
			if "DET_ana_id" in coref and (not "DET_ana_type" in coref or coref["DET_ana_type"]=="DIRECT"):
				ids.append(coref["DET_ana_id"])
			#for key in ["ant_id", "id", "eq", "DET_ant_id", "DET_id", "DET_eq" ]:
				# if we admit @eq, it seems to merge *everything* in the next step. Not sure what this means, maybe not coreference, but type identity?
			for key in ["ant_id", "id", "DET_ant_id", "DET_id" ]:
				if key in coref:
					ids.append(coref[key])
			for x in ids:
				if len(ids)==1:
					eqs.append((x,x))
				for y in ids:
					if x!=y:
						eqs.append((x,y))

			# make sure all ids for zeros are declared
			for zero_key in ["ga","o","ni"]:
				if zero_key in coref and zero_key+"_type" in coref and coref[zero_key+"_type"]=="zero":
					zero=coref[zero_key]
					if not zero in zero_ids:
						zero_ids.append(zero)
	ids=sorted(set([ eq[0] for eq in eqs ] + [ eq[1] for eq in eqs ] + zero_ids))

	# normalize IDs to smallest ID per cluster (numerical IDs, only)
	id2cluster={ int(x):int(x) for x in ids if re.match("^[0-9]+",x)}

	complete=False
	while(not complete):
		complete=True
		for x,y in eqs:
			try:
				x=int(x)
				y=int(y)
				ids=set([x,y,id2cluster[x], id2cluster[y]])
				if len(ids)>0:
					cluster=min(ids)
					for id in ids:
						if id2cluster[id] > cluster:
							id2cluster[id]=cluster
							complete=False
			except Exception as e:
				raise e

	id2cluster= { str(key):str(val) for key,val in id2cluster.items() }
	for e in [ eq[0] for eq in eqs ] + [eq[1] for eq in eqs ]:
		if not e in id2cluster:
			id2cluster[e]=e

	# create corefud, with head-based annotation
	corefud = []
	for sentence in merged:
		corefud.append([])
		for row in sentence:
			coref={ feat.split("=")[0] : "=".join(feat.split("=")[1:]).strip('"') for feat in row[10].split() if "=" in feat}
			if len(coref)==0:
				corefud[-1].append(row[:10])
				continue

			entity=""
			for feat in ["id", "DET_id"]:
				if feat in coref: 
					try:
						entity=id2cluster[coref[feat]]
					except KeyError:
						sys.stderr.write(f"warning: key {coref[feat]} is not a known cluster id\n")
						entity=coref[feat]
			if entity=="":
				if "ana_id" in coref and (not "ana_type" in coref or coref["ana_type"]=="DIRECT"):
					entity=id2cluster[coref["ana_id"]]
			if entity=="":
				if "DET_ana_id" in coref and (not "DET_ana_type" in coref or coref["DET_ana_type"]=="DIRECT"):
					entity=id2cluster[coref["DET_ana_id"]]
			if entity=="":
				if "ant_id" in coref:
					entity=id2cluster[coref["ant_id"]]
			if entity=="":
				if "DET_ant_id" in coref:
					entity=id2cluster[coref["DET_ant_id"]]

			if entity!="":
				entity=f"Entity=(e{entity})"
			else:
				entity="_"

			zeros=[]
			for feat in ["ga","o","ni"]:
				if feat in coref and feat+"_type" in coref and coref[feat+"_type"]=="zero":
					if coref[feat] in id2cluster:
						zeros.append(id2cluster[coref[feat]]+"-zero-"+feat)
						# otherwise, this is exophoric, ignored
			if len(zeros)>0:
				if entity=="_":
					entity=f"Entity="
				for zero in sorted(set(zeros)):
					entity+=f"({zero})"

			corefud[-1].append(row[:9]+[entity])

	# expand spans to include determiners, adjectives, classifiers, numerals (and anything between)
	expanded=[]
	for snr,sentence in enumerate(corefud):
		expanded.append([ row[0:9]+["_"] for row in sentence ] )
		for wnr, row in enumerate(sentence):
			feats={ feat.split("=")[0] : "=".join(feat.split("=")[1:]) for feat in row[9].split("|") if "=" in feat }
			if "Entity" in feats:
				for id in re.sub(r"[()]"," ",feats["Entity"]).split():
					if "-zero-" in id:
						# don't expand zeros
						 if "Entity" in expanded[-1][wnr][9]:
						 	expanded[-1][wnr][9]+=f" ({id})"
						 else:
						 	expanded[-1][wnr][9]=f"Entity=({id})"
					else: # expand non-zeros
						id=re.sub(r"[^0-9]","",feats["Entity"])
						deps=[int(row[0])-1]
						for dep in sentence:
							if dep[6]==row[0] and dep[7].split(":")[0] in ["amod","det","num","clf", "nmod", "compound", "flat", "acl"]:
								deps.append(int(dep[0])-1)
						deps.sort()
						start=deps[0]
						end=deps[-1]
						
						start_anno=f"({id})"
						end_anno=f"({id})"
						if start<end: 
							start_anno=start_anno[:-1]
							end_anno=end_anno[1:]

						#print(expanded[-1][start])
						if "Entity" in expanded[-1][start][9]:
							expanded[-1][start][9]+=" "+start_anno
						else:
							expanded[-1][start][9]="Entity="+start_anno
						
						if "Entity" in expanded[-1][end][9]:
							expanded[-1][end][9]+=" "+end_anno
						else:
							expanded[-1][end][9]="Entity="+end_anno

	# sort and write back into corefud
	for snr,sentence in enumerate(expanded):
		for wnr, row in enumerate(sentence):
			corefud[snr][wnr][9]="_"
			feats={ feat.split("=")[0] : "=".join(feat.split("=")[1:]) for feat in row[9].split("|") if "=" in feat }
			if "Entity" in feats:
				score_annos=[]
				for anno in sorted(set(feats["Entity"].split())):
					score=0
					if anno.endswith(")"):
						score=-1
						if anno.startswith("("):
							score=0
					elif anno.startswith("("):
						score=1
					else:
						sys.stderr.write(f"warning: invalid Entity reference {anno}\n")
						sys.stderr.flush()
					score_annos.append((score,anno))
				score_annos.sort()
				corefud[snr][wnr][9]="Entity="+"".join([a for _,a in score_annos])

	# expand zeros into separate tokens (akin to AnCora)
	expanded=[]
	for sentence in corefud:
		expanded.append([])
		for row in sentence:
			expanded[-1].append(row)
			if "Entity" in row[9]:
				feats={ feat.split("=")[0] : "=".join(feat.split("=")[1:]) for feat in row[9].split("|") if "=" in feat }
				zeros=[ e for e in re.sub(r"[()]"," ",feats["Entity"]).split() if "-zero-" in e ]
				if len(zeros)>0:
					nonZeros=feats["Entity"]
					for zero in zeros:
						zero=f"({zero})"
						while(zero in nonZeros):
							nonZeros=nonZeros[:nonZeros.index(zero)]+nonZeros[nonZeros.index(zero)+len(zero):]
					if len(nonZeros)==0:
						expanded[-1][-1][9]="_"
					else:
						expanded[-1][-1][9]="Entity="+nonZeros
					head=row[0]
					for nr,zero in enumerate(zeros):
						dep="dep"
						if "zero-ga" in zero:
							dep="nsubj"
						if "zero-o" in zero:
							dep="obj"
						if "zero-ni" in zero:
							dep="iobj"
						row=["_"]*10
						row[0]=head+"."+str(nr+1)
						row[3]="PRON"
						row[6]=head
						row[7]=dep
						entity=zero
						if "(" in entity: entity=entity.split("(")[1]
						if ")" in entity: entity=entity.split(")")[0]
						if "-" in entity: entity=entity.split("-")[0]
						row[9]=f"Entity=({entity})"
						expanded[-1].append(row)
	corefud=expanded
			
	# spellout
	for sentence in corefud:
		for row in sentence:
			if row[0]=="1": 
				print()
				print("# text: "+" ".join([r[1] for r in sentence ]))
			print("\t".join(row))
		print()

	print()
