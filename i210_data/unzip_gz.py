import gzip    
import os
#for filename in ['probe_data_I210.20171021.waynep1.csv.gz']:
#TODO: housekeeping. make this into a function. save it not inside the same folder as data.

folder = '10_21_2017'
for filename in os.listdir(folder):
    filename = folder + '/' + filename
    with gzip.open(filename, 'rt') as f:
        data = f.read()
    with open(filename[:-3], 'wt') as f:
      f.write(data)