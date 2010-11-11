#!/usr/bin/env python
from lucene import \
    QueryParser, IndexSearcher, StandardAnalyzer, SimpleFSDirectory, File, \
    VERSION, initVM, Version

def execute_query(query):
	
	STORE_DIR = "index"
    initVM()
    print 'lucene', VERSION
    directory = SimpleFSDirectory(File(STORE_DIR))
    searcher = IndexSearcher(directory, True)
    analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
    results = get_results(searcher, analyzer, query)
    searcher.close()
	return results

def get_results(searcher, analyzer, query_command):
	#command = 'religion:vedas.json AND contents: death' #raw_input("Query:")
	query = QueryParser(Version.LUCENE_CURRENT, "contents", analyzer).parse(query_command)
	scoreDocs = searcher.search(query, 50).scoreDocs

	for scoreDoc in scoreDocs:
		doc = searcher.doc(scoreDoc.doc)
		print 'religion', doc.get('religion')
		print 'contents:', doc.get("contents")