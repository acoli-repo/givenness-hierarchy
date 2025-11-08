import sys,os,re,statistics
from pprint import pprint

""" add (difference from) canonical salience, i.e., average, for selected metrics """

COLS=["CAT","TEXT","UPOS","XPOS","FEATS","EDGE","DEPTH","RD","TP_1","TP_20","TP", "RI_20","WO_RELATIVE","WO_PERIPHERY","WO_VERB",
	  "hsal_RD","ssal_TP_1","ssal_TP_20","ssal_TP","hsal_lin","ssal_lin_20","hsal_RI_20","ssal_RI_40","ssal_FF_20" ]

target_col=COLS[0]
files=sys.argv[1:]
stdev=True

if len(files)>0:
	if files[0] in COLS:
		target_col=files[0]
		files=files[1:]
		sys.stderr.write("target column "+target_col+"\n")

if len(files)==0:
	sys.stderr.write("reading analyzed TSV files from stdin\n")
	files=[sys.stdin]

sys.stderr.flush()

cat2metric2observations={}

buffer=""

for file in files:
	if isinstance(file,str):
		buffer+=f"# {file}\n"
		file=open(file,"rt",errors="ignore")
	for line in file:
		buffer+=line
		line=line.strip()
		if not line.startswith("#") and "\t" in line:
			fields=line.split("\t")
			fields=dict(zip(COLS,fields))
			cat=fields[target_col]
			if not cat in ["PRED","_",""]:# and not "?" in cat and not "(" in cat:

				for k,v in fields.items():
					if k.split("_")[0] in ["hsal","ssal"]:
						if not cat in cat2metric2observations: cat2metric2observations[cat]={}
						if not "TOTAL" in cat2metric2observations: cat2metric2observations["TOTAL"]={}
						if not k in cat2metric2observations[cat]: cat2metric2observations[cat][k]=[]
						if not k in cat2metric2observations["TOTAL"]: cat2metric2observations["TOTAL"][k]=[]
						try:
							cat2metric2observations[cat][k].append(float(v))
							cat2metric2observations["TOTAL"][k].append(float(v))
						except Exception:
							pass

	buffer+="\n"
	file.close()

# csal for selected metrics
metric2cat2avg={}
for metric in ["hsal_lin"]:
	COLS.append(metric+"_diff_avg")
	metric2cat2avg[metric]={}
	for cat in cat2metric2observations:
		if metric in cat2metric2observations[cat]:
			observations=cat2metric2observations[cat][metric]
			metric2cat2avg[metric][cat]=statistics.mean(observations)

# run over all input again and write new TSV to stdout
print("\t".join(COLS))
for line in buffer.split("\n"):
	line=line.strip()
	if not line.startswith("#") and "\t" in line:
		fields=line.split("\t")
		fields=dict(zip(COLS,fields))
		cat=fields[target_col]
		vals=list(fields.values())
		for metric in metric2cat2avg:
			val="_"
			if metric in fields and cat in metric2cat2avg[metric]:
				try:
					val=str(float(fields[metric])-metric2cat2avg[metric][cat])
				except Exception:
					pass
			vals.append(val)
		print("\t".join(vals))
print()
