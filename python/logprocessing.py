#!/usr/bin/env python3

import os
import re
import sys
import json
from pprint import pprint
from functools import reduce

def get_dataframe_from_folder( dir_, meta, query ):
        import pandas as pd
        import io
        
        buffer_ = io.StringIO()
        p = LogProcessor( directory = dir_, meta = meta, query = query, _file = buffer_)

        p.process()
        buffer_.flush()
        buffer_.seek(0)
        
        df = pd.read_csv( buffer_, delimiter=' ', index_col = False)
        buffer_.close()

        return df

class row: pass

def mean(l):
	return reduce(lambda x, y: x + y, l) / float(len(l))

class LogProcessor:
	
	def __init__( self, directory, meta, query, _file = sys.stdout ):
		self._directory = directory
		self._meta = meta
		self._query = query
		self._file = _file
		
		line = query["columns"]
		self._columns = line.split(",")
		tables = set()

		for x in re.findall( "([a-zA-Z_][0-9a-zA-Z_]*)[.]", line ):
			tables.add(x)

		self._file_list = list(tables)
		
	def process( self ):
		"""
		This function will recursively traverse subdirectories from the actual directory (.),
		and will search for log folders. Each time it finds a log folder, it call processDir
		to output the log contents according to the query entered by the user.
		"""
		
		print( self._query["header"], file = self._file )
		self._file.flush()

		for root, dirs, files in os.walk(self._directory):
			path = root.split(os.sep)

			if( root.endswith("logFiles") and ( root.find("template") == -1 ) ):
				LogProcessor._process_dir(root, self._file_list, self._columns, self._file, self._meta)


	def _process_dir( d, files, columns, _file, mapping ):
		
		"""
		This function prints the columns from the log files according to the query
		specified by the user, consulting the meta data to translate the field names
		to the column position in each log
		"""
		fhandles = {}
		
		if( d == "template"):
			return

		for f in files:
			try:
				fhandles[f] = open(d + "/" + mapping["alias"][f], 'r')
			except IOError:
				print ("Error on opening file: " + d + "/" + mapping["alias"][f])
				sys.exit(1)

		flag = True		

		while( flag ):

			for h in fhandles.values():
				line = h.readline()

				if( not line ):
					flag = False
					break

				line = line.rstrip()

				rlist = re.findall(r"-?\d*\.{0,1}\d+", line)

				fileName = os.path.split(h.name)[1]

				rkeys = mapping["columns"][fileName]

				robj = row()
				locals()[mapping["reversealias"][fileName]] = robj			

				i = 0			
				for k in rkeys:					
					if(rkeys[i] == "timestamp"):
						setattr(robj, rkeys[i], int(rlist[i]))
					else:
						if( rkeys[i].endswith("*")):
							col = rkeys[i].replace("*","")

							if(not hasattr(robj, col)):
								l = []
								setattr(robj, col, l)
							else:
								l = getattr(robj, col)

							
							l.append(float(rlist[i]))
						else:
							setattr(robj, rkeys[i], float(rlist[i]))	
					i = i + 1

			if( not flag ):
				break

			for c in columns:
				val = eval(c.strip())
				print( float(val) , end = ' ', file = _file)
				
			print('', file = _file)
			
			_file.flush()

		for h in fhandles.values():
			h.close()
	

class MetadataBuilder:
	_default = {
		"alias": {
			"cpuall": "log_cpu_all.txt",
			"cpuvm1": "log_cpu_ubuntu01.txt",
			"cpuvm2": "log_cpu_ubuntu02.txt",
			"energy": "log_IPMI_all_power.txt",
			"memoryvm1": "log_ubuntu01_memory.txt",
			"memoryvm2": "log_ubuntu02_memory.txt",
			"memory": "log_memory.txt",
			"net": "log_net_br0.txt",
			"netvm1": "log_net_vnet1.txt",
			"netvm2": "log_net_vnet2.txt",
			"io": "log_io.txt",
			"iovm1": "log_io_ubuntu01.txt",
			"iovm2": "log_io_ubuntu02.txt"
		},
		"metadata": {
			"log_cpu_all.txt": "../meta/cpu.json",
			"log_cpu_ubuntu01.txt": "../meta/cpuvm.json",
			"log_cpu_ubuntu02.txt": "../meta/cpuvm.json",
			"log_IPMI_all_power.txt": "../meta/energy.json",
			"log_ubuntu01_memory.txt": "../meta/memory.json",
			"log_ubuntu02_memory.txt": "../meta/memoryvm.json",
			"log_memory.txt": "../meta/memory.json",
			"log_net_br0.txt": "../meta/net.json",
			"log_net_vnet1.txt": "../meta/net.json",
			"log_net_vnet2.txt": "../meta/net.json",
			"log_io.txt": "../meta/io.json",
			"log_io_ubuntu01.txt": "../meta/iovm.json",
			"log_io_ubuntu02.txt": "../meta/iovm.json"
		}
	}

	def __init__( self, mapping = None ):
		if( mapping is None ):
			self._mapping = MetadataBuilder._default
		else:
			self._mapping = mapping

	def _load_metadata( self ):
		self._mapping["columns"] = {}
		for k in self._mapping["metadata"].keys():
			fileName = self._mapping["metadata"][k]

			with open(fileName) as data_file:
				data = json.load(data_file)
				columns = []

				for c in data:
					if( ("list" in c) and (c["list"]) ):
						size = c["size"]
						for i in range(0, size):
							columns.append( c["name"] + "*" )
					else:
						columns.append( c["name"] )

				self._mapping["columns"][k] = columns


			self._mapping["reversealias"] = {}

		for k in self._mapping["alias"].keys():
			self._mapping["reversealias"][self._mapping["alias"][k]] = k
			
		return self._mapping
	
	def load_cpu_cores( self, cores ):
		for i in range( 0, cores):
			self._mapping["alias"]["cpu%d" %  i] = "log_cpu_%d.txt" % i
			self._mapping["metadata"]["log_cpu_%d.txt" % i] = "../meta/cpu.json"	
		
		return self
	
	def build( self ):
		return self._load_metadata()

if __name__ == "__main__":
    m =  MetadataBuilder().load_cpu_cores(32).build()

    query = {
            "header": "timestamp cpu1 io_write io_read net_down net_up memory power",
            "columns": "cpu0.timestamp, 100 - cpu0.idle, io.writet, io.readt, net.download, net.upload, memory.used, mean( energy.power_active )"
    }

    lp = LogProcessor( 
            directory = "../experiments/",
            meta = m,
            query = query)

    lp.process()
