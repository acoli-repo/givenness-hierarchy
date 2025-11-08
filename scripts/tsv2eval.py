import sys,os,re,statistics
from pprint import pprint

DEFAULT_COLS=["CAT","TEXT","UPOS","XPOS","FEATS","EDGE","DEPTH","RD","TP_1","TP_20","TP", "RI_20","WO_RELATIVE","WO_PERIPHERY","WO_VERB",
	  "hsal_RD","ssal_TP_1","ssal_TP_20","ssal_TP","hsal_lin","ssal_lin_20","hsal_RI_20","ssal_RI_40","ssal_FF_20" ]
COLS=DEFAULT_COLS

target_col=COLS[0]
files=sys.argv[1:]
stdev=True

if len(files)>0:
	if files[0] in COLS:
		target_col=files[0]
		files=files[1:]
		sys.stderr.write("target column "+target_col+"\n")

if len(files)>0:
	if not os.path.exists(files[0]):
		if files[0]=="-no_stdev":
			stdev=False
			files=files[1:]
			sys.stderr.write("disable standard deviation\n")

if len(files)==0:
	sys.stderr.write("reading analyzed TSV files from stdin\n")
	files=[sys.stdin]

sys.stderr.flush()

cat2metric2observations={}

for file in files:
	if isinstance(file,str):
		file=open(file,"rt",errors="ignore")
	COLS=DEFAULT_COLS
	for n,line in enumerate(file):
		line=line.strip()
		if n==0 and "\t" in line: # header, optionally preceded by '#'
			my_cols=[ h.strip() for h in ("".join(line.split("#")).strip()).split("\t") ]
			if my_cols[0]=="CAT":
				COLS=my_cols
				line=""
			sys.stderr.write("header set to "+" ".join(COLS)+"\n")
			sys.stderr.flush()
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

	file.close()

header=[]
results=[]
for cat in cat2metric2observations:
	result=[]
	for metric,observations in cat2metric2observations[cat].items():
		if len(observations)>0:
			if len(observations)<10 and cat[-1]!=")": cat=f"({cat})"
			if len(result)==0: result.append(str(len(observations)))
			if not metric in header: header.append(metric)
			try:
				result.append(statistics.mean(observations))
				if stdev: result.append(statistics.stdev(observations))
			except Exception:
				result.append(float(observations[0]))
				if stdev: result.append("_")
	#results.append((2*result[1]*result[3]/(1+result[1]+result[3]),[cat]+result))
	if len(result)>1:
		results.append((result[1],[cat]+result))
	#results.append((result[3],[cat]+result))

results=[ r  for _,r in reversed(sorted(results)) ]

if stdev:
	print("CAT\tFREQ\t"+"\t\t".join(header))
else:
	print("CAT\tFREQ\t"+"\t".join(header))
for result in results:
	result=[ f"{val:1.3f}" if isinstance(val,float) else str(val) for val in result ]
	print("\t".join(result))
