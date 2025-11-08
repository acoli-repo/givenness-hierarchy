import sys,os,re,traceback,json,argparse,lxml
import lxml.etree as etree
import spacy
import spacy_udpipe

from pprint import pprint

""" read one or more *.coref files from stdin or as args, 
	note that we treat line breaks as sentence boundaries,
	calculate (approximative) cognitive status according to Gundel et al. (1993) 
	TODO: parse, so that we can find the subject of the preceding utterance
"""

class ConfigurationException(Exception):
	pass

class OntoNotesAnalyzer:

	def __init__(self, config: dict):
		""" config: dict with
				"parser" -> "tool" {"spacy" or "spacy_udpipe"}, "model" 
				"patterns" -> category2feat2patterns
				and category2feat2patterns = category -> [ feat -> pattern ]* 
		"""

		if not "patterns" in config.keys():
			raise ConfigurationException(f'did not find key "patterns" in dict with '+"{"+",".join(sorted(config.keys()))+"}")

		self.category2feat2patterns=config["patterns"]

		if not "parser" in config.keys():
			raise ConfigurationException(f'did not find key "parser" in dict with '+"{"+",".join(sorted(config.keys()))+"}")
		
		if not "tool" in config["parser"].keys():			
			raise ConfigurationException(f'did not find key "tool" in config["parser"] with '+"{"+",".join(sorted(config["parser"].keys()))+"}")

		if not "model" in config["parser"].keys():			
			raise ConfigurationException(f'did not find key "model" in config["parser"] with '+"{"+",".join(sorted(config["parser"].keys()))+"}")

		self.parse_for_refexp=False
		feats=[]
		for feat2patterns in self.category2feat2patterns.values():
			for f2p in feat2patterns:
				for f in f2p:
					if not f in feats:
						feats.append(f)
		for feat in ["UPOS","UPOSES","XPOS","XPOSES","LEMMA","LEMMAS"]:
			if feat in feats:
				self.parse_for_refexp=True
				break

		sys.stderr.write(f"loading {config['parser']['tool']} model {config['parser']['model']}\n")
		sys.stderr.flush()

		if config["parser"]["tool"]=="spacy":
			try:
				self.parser=spacy.load(config["parser"]["model"])
			except Exception as e:
				raise ConfigurationException(f"loading model {config['model']} failed, try to install with `python -m spacy download {config['model']}`")
		elif config["parser"]["tool"]=="spacy_udpipe":
			try:
				self.parser=spacy_udpipe.load(config["parser"]["model"])
			except AssertionError:
				spacy_udpipe.download(config["parser"]["model"])
				self.parser=spacy_udpipe.load(config["parser"]["model"])
		else:
			raise ConfigurationException(f"unsupported parser '{config['parser']['tool']}', use either 'spacy' or 'spacy_udpipe'")

		# change parser to use whitespace tokenization
		self.parser.tokenizer=spacy.tokenizer.Tokenizer(self.parser.vocab, token_match=re.compile(r'\S+').match)

	def get_ref_exp(self,form:str):
		# TODO: parse and analyse
		upos="_"
		uposes="_"
		xpos="_"
		xposes="_"
		lemma="_"
		lemmas="_"

		if self.parse_for_refexp:
			parsed=self.parser(form)
			uposes=[ tok.pos for tok in parsed ]
			xposes=[ tok.pos for tok in parsed ]
			lemmas=[ tok.lemma for tok in parsed ]
			for tok in parsed:
				if tok.head==tok:
					upos=tok.pos
					xpos=tok.pos
					lemma=tok.lemma

		for category, feat2patterns in self.category2feat2patterns.items():
			if isinstance(feat2patterns,list):
				for feat2pattern in feat2patterns:
					feat2pattern = { f:p for f,p in feat2pattern.items() if f in ["LCASED","TEXT"]}
					if len(feat2pattern)>0:
						all_fullfilled=True
						for f,p in feat2pattern.items():
							if f=="TEXT" and not re.match(feat2pattern[f],form.strip()): 			all_fullfilled=False
							if f=="LCASED" and not re.match(feat2pattern[f],form.lower().strip()): 	all_fullfilled=False
							if f=="UPOS" and not re.match(feat2pattern[f], upos.strip()):			all_fullfilled=False
							if f=="XPOS" and not re.match(feat2pattern[f], xpos.strip()):			all_fullfilled=False
							if f=="LEMMA" and not re.match(feat2pattern[f], lemma.strip()):			all_fullfilled=False
							if f=="UPOSES" and not re.match(feat2pattern[f], uposes.strip()):		all_fullfilled=False
							if f=="XPOSES" and not re.match(feat2pattern[f], xposes.strip()):		all_fullfilled=False
							if f=="LEMMAS" and not re.match(feat2pattern[f], lemmas.strip()):		all_fullfilled=False
						if all_fullfilled:
							return category
		return "other"

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

	def analyze(self, text, debug=False):
		""" category: cognitive status,
			feat2patterns: list of feat2pattern, interpreted as logical "OR",
			feat2pattern: feature-value pairs, interpreted as logical "AND",
			note: feat/category "COMMENT" is ignored """

		lines=text.split("\n")
		lines=[l.strip() for l in lines ]
		lines=[l for l in lines if l!="" and not l.startswith("<TEXT") and not l.startswith("</TEXT") ]
		id2chain={}

		for nr,line in enumerate(lines):
			line="<line>"+line+"</line>"
			try:
				line=etree.fromstring(line)
				text=" ".join(line.xpath("//text()")).strip()
				toks=text.split()
				text=" ".join(toks)				

				parsed=None
				if self.parser!=None:
					parsed=self.parser(text)
				
				# path to root, core deps only
				paths=["_"]*len(text.split())
				if parsed!=None:
					paths=[]
					for tok in parsed: 
						path=tok.dep_
						while(tok!=tok.head):
							tok=tok.head
							path=tok.dep_.split(":")[0]+"."+path
						paths.append(path)

				for ref in line.xpath("//COREF"):
					id=ref.attrib["ID"]
					type=ref.attrib["TYPE"]
					form=" ".join(ref.xpath(".//text()"))
					form=" ".join(form.split()).strip()
					first_tok=toks.index(form.split()[0])
					last_tok=first_tok+toks[first_tok:].index(toks[-1])
					gr="other"
					if last_tok-first_tok > len(form.split()):
						first_tok=last_tok-len(form.split())
					if "ROOT.nsubj" in paths[first_tok:last_tok+1]:
						gr="nsubj"
					if type!="APPOS": # only IDENT
						if not id in id2chain: id2chain[id]=[]			
						id2chain[id].append((nr+1,type,form,gr,self.get_ref_exp(form)))
			except lxml.etree.XMLSyntaxError:
				pass

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
args=argparse.ArgumentParser(description="""predict cognitive status according to GH from OntoNotes coref annotation, using a JSON configuration file for parser configuration and feature extraction""")
args.add_argument("files", type=str, nargs="*", help="ontonotes coref files", default=[])
args.add_argument("-l", "--language", type=str, help="language")
args.add_argument("-d","--debug", action="store_true", help="debug mode")
config=os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.json")
args.add_argument("-c","--config", type=str, nargs="?", help="JSON configuration file with Spacy model and extraction patterns for referring expressions with category -> [ (feature, pattern)* ], defaults to "+config, default=config)
args=args.parse_args()

with open(args.config,"rt") as input:
	config=json.load(input)

if not args.language in config:
	sys.stderr.write(f"error: did not find language {args.language} in configuration. use one of "+",".join(sorted(config.keys()))+"\n")
	sys.exit(1)

try:
	analyzer=OntoNotesAnalyzer(config[args.language])
except ConfigurationException as e:
	sys.stderr.write(str(e)+" while initializing OntoNotesAnalyzer\n")
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
		line=line.strip()
		if(line.startswith("<TEXT")):
			if len(text.strip())>0:
				analyzer.analyze(text,debug=args.debug)
			text=line+"\n"
		elif text.startswith("<TEXT"):
			text+=line+"\n"
	if len(text.strip())>0:
		analyzer.analyze(text,debug=args.debug)
	file.close()

#me.analyze(debug=DEBUG)