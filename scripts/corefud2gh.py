import sys,os,re,traceback,json,argparse,lxml
import lxml.etree as etree
from pprint import pprint


from pprint import pprint

""" read one or more Coref-UD files from stdin or as args, 
	use CoNLL-U sentence breaks,
	calculate (approximative) cognitive status according to Gundel et al. (1993)
	we don't parse, but rely on the existing CoNLL-U annotation
"""

class ConfigurationException(Exception):
	pass

class CorefUDAnalyzer:

	def __init__(self, config: dict):
		""" config: dict with
				"patterns" -> category2feat2patterns
				and category2feat2patterns = category -> [ feat -> pattern ]* 
		"""

		if not "patterns" in config.keys():
			raise ConfigurationException(f'did not find key "patterns" in dict with '+"{"+",".join(sorted(config.keys()))+"}")

		self.category2feat2patterns=config["patterns"]

	def get_ref_exp(self,rows:list):
		""" words: list of "\t"-split CoNLL-U rows for one referring expression """

		form=" ".join([row[1] for row in rows ])
		lemmas=" ".join([row[2] for row in rows ])
		uposes=" ".join([row[3] for row in rows ])
		xposes=" ".join([row[4] for row in rows ])
		feats=" ".join([row[5] for row in rows ])
		
		id2head={ row[0]:row[6] for row in rows if re.match(r"^[0-9]+$$",row[0]+row[6])}
		head2deps={row[0]:1 for row in rows }
		complete=False
		while not complete:
			complete=True
			for d in list(head2deps):
				if d in id2head:
					h = id2head[d]
					if h in head2deps:
						head2deps[h]+=head2deps.pop(d)
						complete=False

		head = sorted(head2deps)[0]
		for h,deps in sorted(head2deps.items()):
			if deps>head2deps[head]:
				head=h

		# print("HEAD:",head)
		upos=[ row[3] for row in rows if row[0]==head ][0]
		xpos=[ row[4] for row in rows if row[0]==head ][0]
		lemma=[ row[2] for row in rows if row[0]==head ][0]
		feat=[row[5] for row in rows if row[0]==head][0]

		for category, feat2patterns in self.category2feat2patterns.items():
			if isinstance(feat2patterns,list):
				for feat2pattern in feat2patterns:
					feat2pattern = { f:p for f,p in feat2pattern.items() if f in ["LCASED","TEXT","LEMMA", "LEMMAS","UPOS", "UPOSES", "XPOS", "XPOSES", "FEAT", "FEATS" ]}
					if len(feat2pattern)>0:
						all_fullfilled=True
						for f,p in feat2pattern.items():
							if f=="TEXT" and not re.match(feat2pattern[f],form.strip()): 			all_fullfilled=False
							if f=="LCASED" and not re.match(feat2pattern[f],form.lower().strip()):	all_fullfilled=False
							if f=="LEMMA" and not re.match(feat2pattern[f],lemma.strip()):			all_fullfilled=False
							if f=="LEMMAS" and not re.match(feat2pattern[f],lemmas.strip()):		all_fullfilled=False
							if f=="XPOS" and not re.match(feat2pattern[f],xpos.strip()):			all_fullfilled=False
							if f=="XPOSES" and not re.match(feat2pattern[f],xposes.strip()):		all_fullfilled=False
							if f=="UPOS" and not re.match(feat2pattern[f],upos.strip()):			all_fullfilled=False
							if f=="UPOSES" and not re.match(feat2pattern[f],uposes.strip()):		all_fullfilled=False
							if f=="FEAT" and not re.match(feat2pattern[f],feat.strip()):			all_fullfilled=False
							if f=="FEATS" and not re.match(feat2pattern[f],feats.strip()):			all_fullfilled=False
						if all_fullfilled:
							return category
		return "other"

	# unchanged from ontonotes2gh.py
	def chain2statuses(self, chain:list):
		""" called with a list of tuples:
				line: int with sentence number
				type: warning if not IDENT
				form: surface string
				gr: grammatical role, we only check whether this is nsubj or csubj
		"""
		result=[]
		for nr,(line,type,form,gr,ref) in enumerate(chain):
			
			status=None
			
			# IN FOCUS
			if nr > 0:
				# $r$ is grammatical subject (or morphosyntactically marked topic or focus) of the preceding utterance
				if len( [l for l,t,f,g,r in chain[:nr] if l==line-1 and "subj" in g.lower() ])>0: 
					status="IN FOCUS" 
					
				# $r$ has been mentioned previously in the same utterance
				if chain[nr-1][0]==line: 
					status="IN FOCUS"

				# $r$ is mentioned in each of the two immediately preceding utterances
				if 	line-2 in [ l for l,_,_,_,_ in chain ] and \
					line-1 in [ l for l,_,_,_,_ in chain ]: 
					status="IN FOCUS"

				# DON'T:
				# $r$ is the event denoted by the immediately preceding utterance
		   	
		   	# ACTIVATED
			if status==None and nr > 0:

				# $r$ is mentioned in one of the two preceding utterances
				if 	line-2 in [ l for l,_,_,_,_ in chain ] or \
					line-1 in [ l for l,_,_,_,_ in chain ]: 
					status="ACTIVATED"

				# DON'T:
				# $r$ is something in the immediate spatio-temporal context that is activated by means of a simultaneous gesture or eye gaze. (Approximation: At this stage, we work with written text, so no guestures or eye gaze can be taken into consideration by the recipient.)
				# $r$ is a proposition, fact, or speech act associated with the eventuality (event or state) denoted by the immediately preceding utterance.

			# FAMILIAR
			if status==None and nr > 0:
				# $r$ was previously mentioned in the discourse
				status="FAMILIAR"

				# DON'T
				# $r$ can be assumed to be known by the hearer through background knowledge or shared personal experience.

			# UNIQUE
			if status==None:
				# $e$ contains adequate descriptive/conceptual content to create a unique referent. (Approximation: $e$ contains a lexical element in addition to its syntactic head, e.g., an adjective modifying a noun, a relative clause modifying a pronoun, or the combination of a surname with a given name)
				# approx: at least four words
				if len(form.strip().split())>3:
					status="UNIQUE"

				# DON'T
				# $r$ is linked by association (bridging inference) with an already activated referent. (Approximation: We limit this to lexical associations, i.e., $e$ contains a possessive expression or a prepositional phrase; in the latter case, this criterion co-incides with the other criterion.)

			# REFERENTIAL 
			if status==None:
				# $r$ is mentioned subsequently in the discourse
				if nr < len(chain)-1:
					status="REFERENTIAL"

				# DON'T
				# it is evident from the context that the speaker intends to refer to some specific entity. (Approximation: Normally, such explicit intention is emphasized by the speaker to indicate that $r$ will play a role in future discourse, and if successful, this coincides with the first criterion.)

			# TYPE IDENTIFIABLE
			if status==None:
				# the sense of $e$ (the descriptive/conceptual content it encodes) is understandable. (Approximation: every [remaining] referring expression.)
				status="TYPE IDENTIFIABLE"

			result.append(status)
		return result

	def get_path(self, wid: str, sentence:list):
		""" wid is string, as used in sentence
			sentence is a list of rows, with each row a list of (column) values
		"""
		result="_"

		dep2head={ row[0]:row[6] for row in sentence if len(row)>6 and re.match(r"^[0-9]+$",row[0]+row[6])}
		row2edge={ row[0]:row[7].split(":")[0] for row in sentence if len(row)>7}
		result=None
		
		# to break cycles
		wids=[wid]

		while wid in dep2head:
			if result==None:
				result=row2edge[wid]
			else:
				result=row2edge[wid]+"."+result
			if dep2head[wid] in wids or dep2head[wid]=="0":
				break
			wid=dep2head[wid]
			wids.append(wid)
		
		result="_"
		try: 
			result="ROOT."+".".join(result.split(".")[1:]) # normalize first dependency to ROOT, as in Spacy
		except Exception:
			pass

		return result

	def analyze(self, text, debug=False):
		""" text: complete CoNLL-U document

			category: cognitive status,
			feat2patterns: list of feat2pattern, interpreted as logical "OR",
			feat2pattern: feature-value pairs, interpreted as logical "AND",
			note: feat/category "COMMENT" is ignored """

		sentences=[[]]
		for line in text.split("\n"):
			line=line.strip()
			if line=="" and len(sentences[-1])>0:
				sentences.append([])
			line=line.strip()
			if "\t" in line and line[0] in "0123456789?*": # added ?* for alignment errors with KoCoNovel UD annotations
				fields=line.split("\t")
				sentences[-1].append(fields)

		id2chain={}

		for nr,sentence in enumerate(sentences):
			openid2rows={}
			for row in sentence:
				if len(row)<9:
					raise Exception(f"row {row} doesn't have 10 columns")
				miscs=row[9].split("|")
				wid=row[0]
				for feat in miscs:
					if feat.startswith("Entity="):
						if debug:
							print("ENTITY:",row)
						annos=[""]
						for c in feat.split("=")[1].strip():
							if c=="(":
								if len(annos[-1])>0:
									annos.append("")
							annos[-1]+=c
							if c==")":
								annos.append("")
						for id in openid2rows:
							if not id in "|".join(annos):
								annos.append(id)
						annos=[anno.strip() for anno in annos if len(anno.strip())>0]

						for anno in annos:
							id="".join(anno.split("("))
							id="".join(id.split(")"))
							id=id.split("-")[0]
							id=id.strip()
							if debug:
								print(anno,"->",id)
							if anno.startswith("("):
								openid2rows[id]=[]
							elif not id in openid2rows:
								sys.stderr.write(f"warning: id {id} from anno {anno} not among {sorted(openid2rows.keys())}\n")
								openid2rows[id]=[]
							path=self.get_path(wid, sentence) # wid is string, as used in sentence
							openid2rows[id].append(row+[path])
							if anno.endswith(")"):
								if not id in id2chain: id2chain[id]=[]
								gr="other"

								for path in [ row[10] for row in openid2rows[id] ]:
									if "root.nsubj" in path:
										gr="nsubj"
										break
								id2chain[id].append((nr+1, 	# sentence nr \
													"IDENT",# type \
													" ".join([ row[2] for row in openid2rows[id] ]), # form \
													gr,
													self.get_ref_exp(openid2rows[id])))
								


		ref_form_statuses=[]
		for id,chain in id2chain.items():
			refexps=zip(chain,self.chain2statuses(chain))

			if debug:
				print(id)
				pprint(list(refexps))
				print()

			for (sid,type,form,gr,ref),status in refexps:
				ref_form_statuses.append((ref,form,status))

		if not debug:
			for r,f,s in ref_form_statuses:
				print(f"{r}\t{f}\t{s}")

import argparse
args=argparse.ArgumentParser(description="""predict cognitive status according to GH from CorefUD annotation, using a JSON configuration file for parser configuration and feature extraction""")
args.add_argument("files", type=str, nargs="*", help="CorefUD files", default=[])
args.add_argument("-l", "--language", type=str, help="language")
args.add_argument("-d","--debug", action="store_true", help="debug mode")
config=os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.json")
args.add_argument("-c","--config", type=str, nargs="?", help="JSON configuration file with extraction patterns for referring expressions with category -> [ (feature, pattern)* ], defaults to "+config, default=config)
args=args.parse_args()

with open(args.config,"rt") as input:
	config=json.load(input)

if not args.language in config:
	sys.stderr.write(f"error: did not find language {args.language} in configuration. use one of "+",".join(sorted(config.keys()))+"\n")
	sys.exit(1)

try:
	analyzer=CorefUDAnalyzer(config[args.language])
except ConfigurationException as e:
	sys.stderr.write(str(e)+" while initializing CorefUDAnalyzer\n")
	sys.stderr.flush()
	sys.exit(2)

files=args.files
DEBUG=args.debug
lang=args.language
with open(args.config,"rt",errors="ignore") as input:
	config=json.load(input)

if not lang in config:
	sys.stderr.write(f"error: language {lang} not in config ("+",".join([k for k in config.keys() if k!="COMMENT" ])+")\n")
	sys.exit(2)

if len(files)==0:
	sys.stderr.write("reading from stdin\n")
	files=[sys.stdin]

for file in files:
	if isinstance(file,str):
		sys.stderr.write(f"reading from {file}\n")
		file=open(file,"rt")
	sys.stderr.flush()

	text=""
	for line in file:
		line=line.rstrip()
		if "".join(line.lower().split()).startswith("#newdocid"):
			text=text.strip()
			if len(text)>0:
				analyzer.analyze(text,debug=args.debug)
				text=""
		text+=line+"\n"

	text=text.strip()
	if len(text)>0:
		analyzer.analyze(text,debug=args.debug)

	file.close()