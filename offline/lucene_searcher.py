#!/usr/bin/env python
from lucene import \
    QueryParser, IndexSearcher, StandardAnalyzer, SimpleFSDirectory, File, \
    VERSION, initVM, Version

def execute_query(query, store_dir, result_set_size=1):
	initVM()
	directory = SimpleFSDirectory(File(store_dir))
	searcher = IndexSearcher(directory, True)
	analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
	results = get_results(searcher, analyzer, query, result_set_size)
	searcher.close()
	return results

def get_results(searcher, analyzer, query_command, result_set_size):
	#command = 'religion:vedas.json AND contents: death' #raw_input("Query:")
	query = QueryParser(Version.LUCENE_CURRENT, "contents", analyzer).parse(query_command)
	scoreDocs = searcher.search(query, result_set_size).scoreDocs
	docs = []
	for scoreDoc in scoreDocs:
		doc = searcher.doc(scoreDoc.doc)
		#print searcher.explain(query, scoreDoc.doc).toString()
		docs.append(doc)
		#print 'religion', doc.get('religion')
		#print 'contents:', doc.get("contents")
	return docs

def run():
	docs = execute_query('death', 'index')
	print len(docs)
	for doc in docs:
		print doc
		print 'religion:', doc.get('religion')
		print 'contents:', doc.get('contents')
	
if __name__ == '__main__':
	run()