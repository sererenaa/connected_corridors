import gzip    
import os

#TODO: save it not inside the same folder as data.
#TODO: use separator instead of / to allow for use across windows/linux/

def unzip(folder, files=None):
	"""
	Unzips all .gz files. Applies to all .gz files in a given folder, unless certain files are specified.
	Ex/ unzip('10_2017', ['probe_data_I210.20171022.waynep1.csv.gz'])
	    unzip('10_2017')
	:param folder: A string of the name of the folder within /data where the files to be unzipped are located.
	:param files: A list of .gz files to be unzipped.
	"""

	source = files if files else os.listdir(folder)
	for filename in (file for file in source if file.endswith('.gz')):
		if filename.endswith('.gz'):
		    filename = folder + '/' + filename
		    with gzip.open(filename, 'rt') as f:
		        data = f.read()
		    with open(filename[:-3], 'wt') as f:
		      f.write(data)


unzip('10_2017')