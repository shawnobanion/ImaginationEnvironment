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
from pyUtilities import bIsStopWord,removePunctuation
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
selected_images = []
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
	primary_text = load_passages(filenames[primary_religion], 25)

	for i, p in enumerate(primary_text):		
		passages, joined_passages = [], []
		passages.append(p)
		joined_passage = ' '.join(p)
		joined_passages.append(joined_passage)
		print joined_passage
		clean_passage = removePunctuation(joined_passage)
		for religion in [filenames['Islam'], filenames['Hinduism']]:
			match_passage = get_best_matched_passage_lucene(clean_passage, religion)
			joined_match_passage = ' '.join(match_passage)
			print joined_match_passage
			joined_passages.append(joined_match_passage)
			passages.append(match_passage)
		keywords = get_common_words(joined_passages)
		print keywords
		store_passage(primary_religion, passages, i, keywords, [])
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
		if skip_complete_docs and len(doc.value['images']) == 9:
			continue

		common_words = doc.value['common_words']
		print 'passage num: ', doc.value['passage_num']
		print common_words
        
		search_terms = []
		# pick random common word to use as search term
		if any(common_words):
			search_terms.append(common_words[random.randint(0, len(common_words) - 1)])
		else:
			# no common words exist, so select a random word in passage
			passage_text_filtered = clean_text(' '.join(doc.value['passages'][0]))
			search_terms.append(passage_text_filtered[random.randint(0, len(passage_text_filtered) - 1)])

		print search_terms
		filenames = get_google_images_by_text(' '.join(search_terms), 9, 1)
		doc_to_update = couchdb_util.get_doc(db, doc.id)
		doc_to_update['images'] = filenames
		doc_to_update['image_search_terms'] = search_terms
		couchdb_util.update_doc(db, doc_to_update)
		print

def crop_and_save_image(image_url, num_copies):
    file_ending = image_url.rpartition('.')[-1]
    out_filenames = ['%s_%s.%s' % (int(time.time() * 1000), i, file_ending) for i in range(num_copies)]
    if not utils.crop_images(image_url, 1024, 768, False, *[os.path.join(config.IMAGE_DIR, f) for f in out_filenames]):
		return None
    print 'saved to', out_filenames
    return out_filenames

"""
def get_images_by_text(text, num_of_images):
    urls = []
    #text = utils.replace_special_chars(text)
    #text = utils.strip_all_stop_words(text)
    count = 0
    try:
        for photo in _flickr.walk(text=text, sort=SORT_BY, content_type='1', safe_search=SAFE_SEARCH_FILTER):
            count += 1
            photo_id = photo.attrib['id']
            if photo_id in selected_images:
                continue
            (width, height), url = get_image_info(photo)
            if url:
                if width > min_original_width and height > min_original_height:
                    selected_images.append(photo_id)
                    urls.append(url)
                    if len(urls) == num_of_images:
                        break
    except Exception, e:
            print 'An error occurred while performing a flickr API search', e
    
    print 'picked [' + str(len(urls)) + '] images, looked at [' + str(count) + ']'
    return urls
"""
def get_google_images_by_text(text, max_images, num_copies):
	filenames = []
	
	if text not in _previous_searches.keys():
		_previous_searches[text] = 0
	
	google_search_rsz = 5
	attempts = 0
	MAX_ATTEMPTS = 5
	while len(filenames) / num_copies < max_images: #2mp
		if attempts > MAX_ATTEMPTS: break
		ld = google_image.googleImageSearch(text, 'jpg', '2mp', google_search_rsz, 'default', _previous_searches[text])
		attempts += 1
		# no results
		if not ld or not ld['responseData']:
			_previous_searches[text] += google_search_rsz
			continue
		
		for d in ld['responseData']['results']:
			_previous_searches[text] += 1
			if d['height'] > min_original_height and d['width'] > min_original_width:
				url = d['url']
				result = crop_and_save_image(url, num_copies)
				if result:
					print url
					filenames.extend(result)
					if len(filenames) / num_copies == max_images:
						break

	return filenames

"""
''' Gets the URL of the original version of the image, if it's available '''
def get_image_info(photo_el):
    try:
        sizes_el = _flickr.photos_getSizes(photo_id=photo_el.attrib['id'])
        for size in sizes_el.findall(".//size"):
            if size.attrib['label'] == 'Original' and re.match('.*\.jpg', size.attrib['source']):
                return ((int(size.attrib['width']), int(size.attrib['height'])), size.attrib['source'])
    except Exception, e:
        print e
    return ((-1, -1), '')
"""

############################
### Lucene
############################

def get_best_matched_passage_lucene(text, religion):
	result = execute_lucene_query(format_lucene_query(religion, text))
	if not result:
		# no results in first try, let's remove stop words and try again
		result = execute_lucene_query(format_lucene_query(religion, ' '.join(set(clean_text(text)))))
	return result

def execute_lucene_query(query):
	docs = lucene_searcher.execute_query(query, 'index', 10)
	for doc in docs:
		passage = lucene_doc_to_passage(doc)
		if len(passage) == MAX_LINES_PER_PASSAGE:
			return passage
	return []

def lucene_doc_to_passage(doc):
	return doc.get('contents').split(' ||| ')

def format_lucene_query(religion, text):
	return 'religion:{0} AND {1}'.format(religion, text)

############################
### Text Utilities
############################
	
def get_common_words(passages):
	word_sets = []
	for p in passages:
		word_sets.append(set(clean_text(p)))
	common_words = []
	for set_x, set_y in itertools.combinations(word_sets, 2):
		common_words.extend(set_x.intersection(set_y))
	return list(set(common_words))
		
def clean_text(text):
	result = [word for word in removePunctuation(text.lower()).split(' ') if not bIsStopWord(word)]
	return result
"""
def get_best_matched_passage(passage, passages):
    match_sim, match_keywords, match_index = 0, [], 0
    before_passage = datetime.datetime.now()
    for i, p in enumerate(passages):
        if len(p) == MAX_LINES_PER_PASSAGE:
            cosine.add_document(i, ' '.join(p))
            sim = cosine.classify_document(' '.join(passage))
            if sim[i][0] > match_sim:
                match_sim, match_keywords, match_index = sim[i][0], sim[i][1], i
            cosine.clear()
    match_passage = passages[match_index]
    print datetime.datetime.now() - before_passage
    print ' '.join(match_passage)
    return match_passage, match_keywords
"""

############################
### Database
############################

def store_passage(religion, passages, passage_num, keywords, filenames):
    doc = {'religion':religion, 'passages':passages, 'passage_num':passage_num, 'common_words':keywords, 'images':filenames, 'image_search_terms':[]}
    couchdb_util.store_doc(db, doc)

############################
### Cleanup
############################

def delete_old_images():
    for filename in _images_to_delete:
        if os.path.exists(filename):
            os.remove(filename)
    print 'deleted [' + str(len(_images_to_delete)) + '] images'

def delete_old_documents():
    for doc_id in _documents_to_delete:
        if doc_id in db:
            db.delete(db[doc_id])
    print 'deleted [' + str(len(_documents_to_delete)) + '] couchdb documents'

def flag_images_for_deletion():
    for filename in os.listdir(config.IMAGE_DIR):
        _images_to_delete.append(os.path.join(config.IMAGE_DIR, filename))

def flag_documents_for_deletion():
    for doc in db.view('_design/religions/_view/religions'):
        _documents_to_delete.append(doc.id)

############################
### Auditing
############################

def audit_images():
	failed = 0
	for doc in db.view('_design/religions/_view/religions'):
		fail = False
		if len(doc.value['images']) != 9:
			fail = True
			print 'Passage #: [' + str(doc.value['passage_num']) + ']', 'Doc ID: [' + str(doc.id) + ']', 'Failed due to not enough images.'
		for img in doc.value['images']:
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
		if len(passages) != 3:
			fail = True
			print 'Passage #: [{0}], Doc ID: [{1}], Failed due to not enough passages.'.format(doc.value['passage_num'], doc.id)
		if fail: failed += 1
	print 'Completed passage audit. Number of failed documents: [{0}]'.format(failed)

############################
### Main Entries
############################

def run_passages():
	flag_documents_for_deletion()
	match_passages()
	delete_old_documents()
	audit_passages()

def run_images(skip_complete_docs=False):
	flag_images_for_deletion()
	load_images(skip_complete_docs)
	delete_old_images()
	audit_images()

def run_images_incremental():
    load_images(skip_complete_docs=True);

def run():
    run_passages()
    run_images()

if __name__ == '__main__':
	#run_passages()
	flag_images_for_deletion()
	delete_old_images()
	run_images()
	#audit_images()