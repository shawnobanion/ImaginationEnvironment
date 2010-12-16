import config
import random
import datetime
import simplejson
import couchdb
import flickrapi
import utils
import re
import time
import os
import couchdb_util
import cosine
import sys
import google_image
from pyStemmer import sStem
from pyUtilities import bIsStopWord,removePunctuation,EZGen
import urllib
import lucene_searcher
import itertools

assert config.IMAGE_DIR, "You need to specify a directory to write images to in config.py"
assert os.path.isdir(config.IMAGE_DIR), "Your config.IMAGE_DIR does not specify a valid directory!"
assert config.OFFLINE_DIR, "You need to specify an offline directory"
assert os.path.isdir(config.OFFLINE_DIR), "You need to specify a valid offline directory"
assert config.COUCHDB_CONNECTION_STRING, "You need to specify a couchdb connection string in config.py"
assert config.COUCHDB_DATABASE, "You need to specify a couchdb database name in config.py"

''' Passage parameters '''
MAX_LINES_PER_PASSAGE = 9
MAX_CHARS_PER_LINE = 25

''' Flickr search parameters '''
FLICKR_API_KEY = '0d5347d0ffb31395e887a63e0a543abe'
_flickr = flickrapi.FlickrAPI(FLICKR_API_KEY)
REMOVE_ALL_STOP_WORDS = False
MIN_TAKEN_DATE_FILTER = 946706400 #1/1/2000
SAFE_SEARCH_FILTER = 1
SORT_BY = 'relevance'

''' Image parameters '''
max_original_width, min_original_width = 3600, 1200
max_original_height, min_original_height = 2400, 786

''' Global properties '''
_used_images = {}
_previous_searches = {}
db = couchdb.Server(config.COUCHDB_CONNECTION_STRING)[config.COUCHDB_DATABASE]
filenames = {'Buddhism':'buddha.json', 'Christianity':'bible.json', 'Hinduism':'vedas.json', 'Islam':'quran.json'}
_images_to_delete = []
_documents_to_delete = []

############################
### Passages
############################

def choose_random_book(text):
    index = random.randint(0, len(text) - 1)
    book = text[index]
    text.pop(index)
    return book

def choose_random_verse(book):
    index = random.randint(0, len(book['verses']) - 1)
    verse = book['verses'][index]
    book['verses'].pop(index)
    return verse

def load_passages(filename, max_chapters=sys.maxint):
    text = simplejson.load(open(filename, 'r'))
    #num_passages_yielded = 0
    passages = []
    chapter_count = 0
    for chapter in text:
        lines = []
        curr_line = []
        char_count = 0
        total_verses = len(chapter['verses'])
        
        for verse_num, verse in enumerate(chapter['verses']):
            for word in verse.split():
                if char_count + 1 + len(word) < MAX_CHARS_PER_LINE:
                    curr_line.append(word)
                    char_count += len(word)
                else:
                    lines.append(' '.join(curr_line))
                    if len(lines) == MAX_LINES_PER_PASSAGE:
                        passages.append(lines)
                        #num_passages_yielded += 1
                        #if num_passages_yielded >= max_passages:
                        #    return passages
                        lines = []
                    curr_line = [word]
                    char_count = 0
        
        if any(curr_line):
            lines.append(' '.join(curr_line))
        
        if any(lines):
            passages.append(lines)
        
        chapter_count += 1
        if chapter_count >= max_chapters:
            return passages
    
    return passages

def match_passages():
	before = datetime.datetime.now()

	primary_text, secondary_texts = [], []

	primary_religion = 'Christianity'
	primary_text = load_passages(filenames[primary_religion], 50)

	for i, p in enumerate(primary_text):		
		passages, joined_passages, common_words = [], [], []
		passages.append(p)
		joined_passage = ' '.join(p)
		joined_passages.append(joined_passage)
		print joined_passage
		
		for religion in [filenames['Islam'], filenames['Hinduism']]:
			match_passage = get_best_matched_passage_lucene(removePunctuation(joined_passage), religion)
			joined_match_passage = ' '.join(match_passage)
			print '*** {0} ***'.format(religion.upper())
			print joined_match_passage
			joined_passages.append(joined_match_passage)
			passages.append(match_passage)
			common_words.append(get_common_words(joined_passage, joined_match_passage))
		
		s = set()
		map(lambda x: s.update(x), common_words)
		common_words.reverse()
		common_words.insert(1, list(s))
		print common_words
			
		#print keywords
		store_passage(primary_religion, passages, i, list(s), [], common_words)
		print

	print 'DONE!', datetime.datetime.now() - before
	
# NUMBER OF PASSAGES BY RELIGION:
# Christianity = 27,250
# Islam = 3,080
# Hinduism = 4,723

############################
### Imagery
############################

def load_images(skip_complete_docs=False):
	for doc in db.view('_design/religions/_view/religions'):
		if skip_complete_docs and len(filter(lambda x: x != '', doc.value['images'])) == 9:
			continue

		common_words = doc.value['common_words']
		print 'passage num: ', doc.value['passage_num']
		print common_words
        
		search_terms = []
		search_terms = [w for w in common_words]
		# pick random common word to use as search term
		"""
		if any(common_words):
			search_terms.append(common_words[random.randint(0, len(common_words) - 1)])
		else:
			# no common words exist, so select a random word in passage
			passage_text_filtered = clean_text(' '.join(doc.value['passages'][0]))
			search_terms.append(passage_text_filtered[random.randint(0, len(passage_text_filtered) - 1)])
		"""
		
		print search_terms
		
		image_filenames = []
		for st in doc.value['image_search_terms']:
			image_filenames.extend(get_images(' '.join(st), 3, 1))
		
		doc_to_update = couchdb_util.get_doc(db, doc.id)
		doc_to_update['images'] = image_filenames
		couchdb_util.update_doc(db, doc_to_update)
		print

def crop_and_save_image(image_url, num_copies):
    file_ending = 'jpg' #image_url.rpartition('.')[-1]
    out_filenames = ['%s_%s.%s' % (int(time.time() * 1000), i, file_ending) for i in range(num_copies)]
    if not utils.crop_images(image_url, 1024, 768, False, *[os.path.join(config.IMAGE_DIR, f) for f in out_filenames]):
		return None
    print 'saved to', out_filenames
    return out_filenames


def get_images(text, max_images, num_copies):
	# preferred method
	image_filenames = get_google_images_by_text(text, max_images, num_copies)
	if len(image_filenames) == max_images:
		return image_filenames
		
	# select a random word from the search terms
	words = text.split()
	if len(words) > 1:
		random.shuffle(words)
		while any(words):
			search_term = words.pop()
			image_filenames = get_google_images_by_text(search_term, max_images, num_copies)
			if len(image_filenames) == max_images:
				return image_filenames
				
	# select a random term from the passage
	
	return map(lambda x: '', range(0, max_images))
			
	

def get_google_images_by_text(text, max_images, num_copies):
	filenames = []
	GOOGLE_SEARCH_RSZ = 8
	MAX_ATTEMPTS = 10
	
	for start_index in range(0, GOOGLE_SEARCH_RSZ * MAX_ATTEMPTS + 1, GOOGLE_SEARCH_RSZ):
		ld = google_image.googleImageSearch(text, 'jpg', '2mp', GOOGLE_SEARCH_RSZ, 'default', start_index)

		if not ld or not ld['responseData']:
			continue
		
		for d in ld['responseData']['results']:
			if d['height'] > min_original_height and d['width'] > min_original_width and d['imageId'] not in _used_images:
				url = d['url']
				result = crop_and_save_image(url, num_copies)
				if result:
					print url
					_used_images[d['imageId']] = True
					filenames.extend(result)
					if len(filenames) / num_copies >= max_images:
						break
						
		if len(filenames) / num_copies >= max_images:
			break

	return filenames

############################
### Lucene
############################

def get_best_matched_passage_lucene(text, religion):
	return execute_lucene_query(text, religion)

def execute_lucene_query(text, religion):
	query = format_lucene_query(religion, text)
	docs = lucene_searcher.execute_query(query, 'index', 10)
	for doc in docs:
		assert doc.get('religion') == religion
		passage = lucene_doc_to_passage(doc)
		if len(passage) == MAX_LINES_PER_PASSAGE:
			return passage
	return []

def lucene_doc_to_passage(doc):
	return doc.get('contents').split(' ||| ')

def format_lucene_query(religion, text):
	return 'religion:{0} AND contents:({1})'.format(religion, text)

############################
### Text Utilities
############################

def get_common_words(*texts):
	word_sets = []
	stem_mapping = {}
	result = []
	for text in texts:
		mapping = clean_stem_text(text)
		word_sets.append(set(mapping.keys()))
		for k, v in mapping.iteritems():
			if k in stem_mapping:
				stem_mapping[k].extend(v)
			else:
				stem_mapping[k] = v
	common_words = []
	for set_x, set_y in itertools.combinations(word_sets, 2):
		common_words.extend(set_x.intersection(set_y))	
	for w in common_words:
		result.extend(stem_mapping[w])	
	return list(set(result))

def clean_stem_text(text):
	result = ' '.join([word for word in removePunctuation(text.lower()).split(' ') if not bIsStopWord(word)])
	mapping = sStem(result, True)
	return mapping
		
def clean_text(text):
	return [word for word in removePunctuation(text.lower()).split(' ') if not bIsStopWord(word)]
	
############################
### Database
############################

def store_passage(religion, passages, passage_num, keywords, filenames, image_search_terms):
    doc = {'religion':religion, 'passages':passages, 'passage_num':passage_num, 'common_words':keywords, 'images':filenames, 'image_search_terms':image_search_terms}
    couchdb_util.store_doc(db, doc)

############################
### Cleanup
############################

def delete_old_documents():
    for doc_id in _documents_to_delete:
        if doc_id in db:
            db.delete(db[doc_id])
    print 'deleted [' + str(len(_documents_to_delete)) + '] couchdb documents'

def flag_documents_for_deletion():
    for doc in db.view('_design/religions/_view/religions'):
        _documents_to_delete.append(doc.id)

############################
### Auditing
############################

def audit():
	audit_images()
	audit_passages()

def audit_images():
	failed = 0
	for doc in db.view('_design/religions/_view/religions'):
		fail = False
		if len(filter(lambda x: x != '', doc.value['images'])) != 9:
			fail = True
			print 'Passage #: [' + str(doc.value['passage_num']) + ']', 'Doc ID: [' + str(doc.id) + ']', 'Failed due to not enough images.'
		for img in filter(lambda x: x != '', doc.value['images']):
			filepath = config.IMAGE_DIR + '/' + img
			if not os.path.isfile(filepath):
				print 'Passage #: [' + str(doc.value['passage_num']) + ']', 'Doc ID: [' + str(doc.id) + ']', 'Could not find:', filepath
				fail = True
		if fail: failed += 1
	print 'Completed image audit. Number of failed documents: [' + str(failed) + ']'

def audit_passages():
	failed = 0
	for doc in db.view('_design/religions/_view/religions'):
		fail = False	
		passages = doc.value['passages']
		if len(passages) != 3 or any(filter(lambda x: len(x) == 0, passages)):
			fail = True
			print 'Passage #: [{0}], Doc ID: [{1}], Failed due to not enough passages.'.format(doc.value['passage_num'], doc.id)
		if fail: failed += 1
	print 'Completed passage audit. Number of failed documents: [{0}]'.format(failed)

def delete_unlinked_images():
	linked_images = {}
	for doc in db.view('_design/religions/_view/religions'):
		if any(doc.value['images']):
			linked_images.update(dict(zip(doc.value['images'], EZGen(True))))
	files_to_delete = filter(lambda x: x not in linked_images, os.listdir(config.IMAGE_DIR))		
	for filename in files_to_delete:
		os.remove(os.path.join(config.IMAGE_DIR, filename))
	print 'Deleted {0} images'.format(len(files_to_delete))

############################
### Main Entries
############################

def run_passages(run_audit=True):
	flag_documents_for_deletion()
	match_passages()
	delete_old_documents()
	if run_audit: audit_passages()

def run_images(run_audit=True):
	load_images()
	delete_unlinked_images()
	if run_audit: audit_images()

def run_images_incremental():
	load_images(skip_complete_docs=True);
	delete_unlinked_images()
	audit_images()
	
def run():
    run_passages(False)
    run_images(False)
    audit_passages()
    audit_images()

if __name__ == '__main__':
	#run_passages()
	run_images_incremental()
	#audit_images()