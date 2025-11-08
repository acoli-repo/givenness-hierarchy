import os,sys,re

""" read file(s) from stdin or args, create columns TEXT PRE POST """

files=sys.argv[1:]
if len(files) == 0:
	sys.stderr.write("reading from stdin\n")
	files=[sys.stdin]

for file in files:
	if isinstance(file,str):
		sys.stderr.write(f"reading {file}\n")
		print(f"# file: {file}\n")
		file=open(file,"rt",errors="ignore")
	sys.stderr.flush()

	pre=""
	post=""
	tok=""
	for line in file:
		for c in line:
			if pre.startswith("<") and not pre.endswith(">"):
				pre+=c 
			elif post.startswith("<") and not post.endswith(">"):
				post+=c
				if post.endswith(">") and "</" in post:
					tok=tok.strip()
					pre=" ".join(pre.split()).strip()
					post=" ".join(post.split()).strip()
					if tok=="":  tok="*" # shouldn't happen
					if pre=="":  pre="_"
					if post=="": post="_"
					print(f"{tok}\t{pre}\t{post}")
					tok=""
					pre=""
					post=""
			elif c=="<":
				if len(tok)>0:
					post+=c
				else:
					pre+=c
			elif c in [" ","\t","\n", "\r"]:
				tok=tok.strip()
				if len(tok)>0 or c in ["\n"]:
					tok=tok.strip()
					pre=" ".join(pre.split()).strip()
					post=" ".join(post.split()).strip()
					if tok=="":  tok="*" # shouldn't happen
					if pre=="":  pre="_"
					if post=="": post="_"
					print(f"{tok}\t{pre}\t{post}")
					pre=""
					tok=""
					post=""
				if c == "\n":
					print()
			else:
				tok+=c
	if len((pre+post+tok).strip())>0:
		tok=tok.strip()
		pre=" ".join(pre.split()).strip()
		post=" ".join(post.split()).strip()
		if tok=="":  tok="*" # shouldn't happen
		if pre=="":  pre="_"
		if post=="": post="_"
		print(f"{tok}\t{pre}\t{post}")

	print("\n")
	file.close()
