""" calculate correlation between two columns """

import sys
import numpy
import statistics
import scipy

x=[]
y=[]
header=["",""]
for n,line in enumerate(sys.stdin):
	line=line.strip()
	if n==0 and "\t" in line and not line[0] in "01234567890.":
		header=line.split("\t")
		header=[ f" ({h})" for h in header[0:2]]
		line=""

	line=line.split("#")[0] # no comments
	line.strip()
	if "\t" in line:
		fields=line.split()
		try:
			f0=float(fields[0])
			f1=float(fields[1])
			x.append(f0)
			y.append(f1)
		except Exception:
			pass

print("diagnostics")
print(f"COL 0{header[0]}\n\t{len(x)} values\n\t{len(set(x))} different values\n\tmin {min(x)}\n\tmean {statistics.mean(x)}\n\tmax {max(x)}")
print(f"COL 1{header[1]}\n\t{len(y)} values\n\t{len(set(y))} different values\n\tmin {min(y)}\n\tmean {statistics.mean(y)}\n\tmax {max(y)}")

method2corr_p={}

# based on https://machinelearningmastery.com/how-to-use-correlation-to-understand-the-relationship-between-variables/
# covariance = numpy.cov(x, y)

method2corr_p["Pearson correlation"]=scipy.stats.pearsonr(x, y) # good for linear relationships
method2corr_p["Spearman correlation"]=scipy.stats.spearmanr(x, y) # better for nonlinear relationships
# cf. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html


for method,(corr,p) in method2corr_p.items():
	print(f"{method}\t{corr}\t{p}")

