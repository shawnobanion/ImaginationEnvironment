#!/usr/bin/env python

import sys, os, lucene, threading, time
from datetime import datetime

"""
This class is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.IndexFiles.  It will take a directory as an argument
and will index all of the files in that directory and downward recursively.
It will index on the file path, the file name and the file contents.  The
resulting Lucene index will be placed in the current directory and called
'index'.
"""

class Ticker(object):

    def __init__(self):
        self.tick = True

    def run(self):
        while self.tick:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.0)

class IndexObjects(object):
    """Usage: python IndexFiles <doc_directory>"""

    def __init__(self, objs, storeDir):
		lucene.initVM()
		analyzer = lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)
		if not os.path.exists(storeDir):
			os.mkdir(storeDir)
		store = lucene.SimpleFSDirectory(lucene.File(storeDir))
		writer = lucene.IndexWriter(store, analyzer, True,
		lucene.IndexWriter.MaxFieldLength.LIMITED)
		writer.setMaxFieldLength(1048576)
		self.indexObjs(objs, writer)
		ticker = Ticker()
		print 'optimizing index',
		threading.Thread(target=ticker.run).start()
		writer.optimize()
		writer.close()
		ticker.tick = False
		print 'done'

    def indexObjs(self, objs, writer):	
		for obj in objs:
			doc = lucene.Document()
			for k, v in obj.iteritems():
				doc.add(lucene.Field(k, v, lucene.Field.Store.YES, lucene.Field.Index.ANALYZED))
			writer.addDocument(doc)
		print '{0} documents added'.format(len(objs))

if __name__ == '__main__':
	start = datetime.now()
	try:
		objs = [{ 'contents': 'for thou shalt not Shawn', 'passage_num' : '1'}]
		IndexObjects(objs, "index")
		end = datetime.now()
		print end - start
	except Exception, e:
		print "Failed: ", e
