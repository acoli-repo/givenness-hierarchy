import sys,os,re,statistics
from pprint import pprint
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.pyplot import cm
import numpy as np
import math
from scipy.stats import kde

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
cmap = mpl.colormaps['Greys'].resampled(8)


""" three columns: CAT, x and y
	generate scatter plots for every CAT value 

	optional argument scale (for plots)
	"""


COLS=["CAT","X","Y"]

target_col=COLS[0]
files=sys.argv[1:]

scale=None
if len(files)>0 and not os.path.exists(files[0]):
	scale=float(files[0])
	files=files[1:]
	
if len(files)==0:
	sys.stderr.write("reading analyzed TSV files from stdin\n")
	files=[sys.stdin]

sys.stderr.flush()

cat2x_ys={}

for file in files:
	if isinstance(file,str):
		file=open(file,"rt",errors="ignore")
	for line in file:
		line=line.strip()
		if not line.startswith("#") and "\t" in line:
			fields=line.split("\t")
			if len(fields)>=len(COLS):
				fields=dict(zip(COLS,fields))
				cat=fields["CAT"]
				x=fields["X"]
				y=fields["Y"]

				if not cat in cat2x_ys: cat2x_ys[cat]=[]
				cat2x_ys[cat].append((x,y))

	file.close()

color = cm.rainbow(np.linspace(0, 1, len(cat2x_ys)))

for c,(cat,x_ys) in zip(color,cat2x_ys.items()):
	x=[float(x) for x,_ in x_ys]
	y=[float(y) for _,y in x_ys]

	myscale=1/len(x_ys)
	if scale!=None:
		myscale=float(scale)

#	plt.hist2d(x, y,cmap=cmap)

	# Evaluate a gaussian kde on a regular grid of nbins x nbins over data extents
	k = kde.gaussian_kde((x,y))
	nbins=500
	xi, yi = np.mgrid[min(x):max(x):nbins*1j, min(y):max(y):nbins*1j]
	zi = k(np.vstack([xi.flatten(), yi.flatten()]))

	# plot a density
	print(dir(plt))
	plt.pcolormesh(xi, yi, zi.reshape(xi.shape), cmap=cmap)
	plt.xlabel("col 1")
	plt.ylabel("col 2")
#	plt.xscale("log")
#	plt.yscale("log")
# cf. https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.xscale.html


	plt.show()
