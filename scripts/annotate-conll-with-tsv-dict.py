import sys,os,re

""" we read one or more dictionaries in tsv format from arguments, expecting the word form in the first column
	we read data from stdin,
	we annotate the most frequent (or first) line to every occurrence in the data 
	note that this can be used to resolve ambiguities, e.g., put more specific annotations first, wastebag categories later
"""

files=sys.argv[1:]
tok2anno2freq={}
maxFields=0
for file in files:
	sys.stderr.write(f"reading {file}\n")
	with open(file,"rt",errors="ignore") as input:
		for line in input:
			line=line.strip()
			if not line.strip().startswith("#") and not line.strip()=="":
				fields=line.split("\t")
				maxFields=max(len(fields),maxFields)
				tok=fields[0].strip()
				if not tok in tok2anno2freq: 
					tok2anno2freq[tok]={line:1}
				elif not line in tok2anno2freq[tok]:
					tok2anno2freq[tok][line]=1
				else:
					tok2anno2freq[tok][line]+=1

tok2anno={}
for nr,(tok,anno2freq) in enumerate(tok2anno2freq.items()):
	freq=0
	anno="_"
	for a,f in anno2freq.items():
		if f>freq:
			anno=a
			freq=f
	tok2anno[tok]=anno
	sys.stderr.write(f"\rpruned {nr+1} toks")

sys.stderr.write("\n")

sys.stderr.write("reading CoNLL data to be annotated from stdin\n")
sys.stderr.flush()
for line in sys.stdin:
	if line.split("#")[0].strip()=="":
		print(line.rstrip())
	else:
		fields=line.rstrip().split("\t")
		tok=fields[0].strip()
		anno=[]
		if tok in tok2anno:
			anno=tok2anno[tok].split("\t")
		elif tok.lower() in tok2anno:
			anno=tok2anno[tok.lower()].split("\t")
		while len(anno)<maxFields:
			anno.append("_")		
		print("\t".join(fields+anno))
