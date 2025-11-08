import sys,os,re,statistics
from pprint import pprint
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import math

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

	if len(cat2x_ys[cat])>10:
		gaussian_noise = np.random.normal([0]*len(x+y), statistics.stdev(x+y)/10, len(x+y))
		gaussian_noise_x=gaussian_noise[0:len(x)]
		gaussian_noise_y=gaussian_noise[len(x):]

		for n in range(len(x)):
			x[n]+=gaussian_noise_x
			y[n]+=gaussian_noise_y

	myscale=1/len(x_ys)
	if scale!=None:
		myscale=float(scale)

	plt.scatter(x, y,c=c,label=cat,marker="o",s=scale)

plt.legend()
plt.show()
