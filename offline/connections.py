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
from pyUtilities import bIsStopWord

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
filenames = {'Buddhism':'buddha.json', 'Christianity':config.OFFLINE_DIR + 'bible.json', 'Hinduism':config.OFFLINE_DIR + 'vedas.json', 'Islam':config.OFFLINE_DIR + 'quran.json'}
_images_to_delete = []
_documents_to_delete = []

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

# NUMBER OF PASSAGES BY RELIGION:
# Christianity = 27,250    
# Islam = 3,080
# Hinduism = 4,723

def load_images(skip_complete_docs=False):
    for doc in db.view('_design/religions/_view/religions'):
        
        if skip_complete_docs and len(doc.value['images']) == 9:
            continue

        common_words = doc.value['common_words']
        common_words = [w for w in common_words if len(w) > 1]
        religiousy_stop_words = ['art', 'come', 'forth', 'hast', 'hath', 'let', 'o', 'say', 'shall', 'thee', 'thou', 'thy', 'unto', 'ye']
        filtered_common_words = [w for w in common_words if w not in religiousy_stop_words]
        print 'passage num: ', doc.value['passage_num']
        print filtered_common_words
        
        all_search_terms = []
        if len(filtered_common_words) > 0:
            search_term = filtered_common_words[random.randint(0, len(filtered_common_words) - 1)]
            search_term_stem = sStem(search_term)
            all_search_terms = ([w for w in filtered_common_words if sStem(w) == search_term_stem])
        elif len(common_words) == 0:
            passage_text = ' '.join(doc.value['passages'][0])
            passage_text_filtered = [w for w in passage_text.split() if not bIsStopWord(w)]
            search_term = passage_text_filtered[random.randint(0, len(passage_text_filtered) - 1)]
            all_search_terms.append(search_term)
        else:
            search_term = common_words[random.randint(0, len(common_words) - 1)]
            all_search_terms.append(search_term)

        print search_term
        print all_search_terms
        images = get_google_images_by_text(search_term, 3)
        print images
        filenames = []
        for image in images:
            filenames.extend(crop_and_save_image(image))
        doc_to_update = couchdb_util.get_doc(db, doc.id)
        doc_to_update['images'] = filenames
        doc_to_update['image_search_terms'] = all_search_terms
        couchdb_util.update_doc(db, doc_to_update)
        print

def crop_and_save_image(image_url):
    file_ending = image_url.rpartition('.')[-1]
    out_filenames = ['%s_%s.%s' % (int(time.time() * 1000), i, file_ending) for i in range(3)]
    utils.crop_images(image_url, *[os.path.join(config.IMAGE_DIR, f) for f in out_filenames])
    print 'saved to', out_filenames
    return out_filenames
    
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

def get_google_images_by_text(text, max_images):
	urls = []
	
	# increment start index for search term so we don't get same image twice
	if text in _previous_searches.keys():
		_previous_searches[text] += max_images
	else:
		_previous_searches[text] = 0
		
	ld = google_image.googleImageSearch(text, 'default', '2mp', 3, 'default', _previous_searches[text])
	for d in ld['responseData']['results']:
		url = d['url']
		urls.append(url)
		if len(urls) == max_images:
			break
			
	print 'picked [' + str(len(urls)) + '] images'
	return urls
		
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
		
def match_passages():
    before = datetime.datetime.now()
    
    primary_text, secondary_texts = [], []
    
    primary_religion = 'Christianity'
    primary_text = load_passages(filenames[primary_religion], 3)
    secondary_texts.append(load_passages(filenames['Islam']))
    secondary_texts.append(load_passages(filenames['Hinduism']))

    for i, p in enumerate(primary_text):
        passages, keywords = [], []
        passages.append(p)
        print ' '.join(p)
        for text in secondary_texts:
            match_passage, match_keywords = get_best_matched_passage(p, text)
            passages.append(match_passage)
            keywords.extend(k for k in match_keywords if not k in keywords)
        print keywords
        store_passage(primary_religion, passages, i, keywords, [])
        print

    print 'DONE!', datetime.datetime.now() - before

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

def store_passage(religion, passages, passage_num, keywords, filenames):
    doc = {'religion':religion, 'passages':passages, 'passage_num':passage_num, 'common_words':keywords, 'images':filenames}
    couchdb_util.store_doc(db, doc)

def run_passages():
    flag_documents_for_deletion()
    match_passages()
    delete_old_documents()

def run_images():
    flag_images_for_deletion()
    load_images()
    delete_old_images()

def run_images_incremental():
    load_images(skip_complete_docs=True);

def run():
    run_passages()
    run_images()

if __name__ == '__main__':
    run_images()
