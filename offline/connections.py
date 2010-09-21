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

''' Passage length parameters '''
max_lines_per_passage = 9
max_chars_per_line = 25
max_passages = 1

''' Flickr search parameters '''
flickr_api_key = '0d5347d0ffb31395e887a63e0a543abe'
_flickr = flickrapi.FlickrAPI(flickr_api_key)
remove_all_stop_words = False
min_taken_date_filter = 946706400 #1/1/2000
safe_search_filter = 1
sort_by = 'interestingness-desc'

''' Image parameters '''    
max_original_width, min_original_width = 3600, 1200
max_original_height, min_original_height = 2400, 786

''' Global properties '''
selected_images = []
db = couchdb.Server(config.COUCHDB_CONNECTION_STRING)['imagination']
filenames = {'Buddhism':'buddha.json', 'Christianity':config.OFFLINE_DIR + 'bible.json', 'Hinduism':config.OFFLINE_DIR + 'vedas.json', 'Islam':config.OFFLINE_DIR + 'quran.json'}
images_to_delete = []
documents_to_delete = []

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

def load_passages(filename, max_passages=sys.maxint):
    text = simplejson.load(open(filename, 'r'))
    num_passages_yielded = 0
    passages = []
    #while True:
    for book in text:
        #book = choose_random_book(text)
        lines = []
        curr_line = []
        char_count = 0
        for verse in book['verses']:
            for word in verse.split():
                if char_count + 1 + len(word) < max_chars_per_line:
                    curr_line.append(word)
                    char_count += len(word)
                else:
                    lines.append(' '.join(curr_line))
                    if len(lines) == max_lines_per_passage:
                        #yield lines
                        passages.append(lines)
                        num_passages_yielded += 1
                        if num_passages_yielded >= max_passages:
                            return passages
                        lines = []
                    curr_line = [word]
                    char_count = 0
    return passages

# NUMBER OF PASSAGES BY RELIGION:
# Christianity = 27,250    
# Islam = 3,080
# Hinduism = 4,723

def load_images():
    for doc in db.view('_design/religions/_view/religions'):
        line_index = doc.value['selected_line']
        passage = doc.value['passage']
        line = passage[line_index]
        images = get_images_by_text(line, 3)
        print images
        filenames = []
        for image in images:
            filenames.extend(crop_and_save_image(image))
        doc_to_update = couchdb_util.get_doc(db, doc.id)
        doc_to_update['images'] = filenames
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
    text = utils.replace_special_chars(text)
    text = utils.strip_all_stop_words(text)
    print text
    count = 0
    try:
        for photo in _flickr.walk(text=text, sort=sort_by, content_type='1', min_taken_date=min_taken_date_filter, safe_search=safe_search_filter):
            (width, height), url = _sizeAndURLOfImage(photo)
            count += 1
            if url:
                photo_id = photo.attrib['id']
                if not photo_id in selected_images and width > min_original_width and height > min_original_height:
                    selected_images.append(photo_id)
                    urls.append(url)
                    if len(urls) == num_of_images:
                        break
    except Exception, e:
            print 'An error occurred while performing a flickr API search', e

    print 'picked [' + str(len(urls)) + '] images, looked at [' + str(count) + ']'
    return urls

''' Gets the URL of the original version of the image, if it's available '''    
def _sizeAndURLOfImage(photo_el):
    try:
        sizes_el = _flickr.photos_getSizes(photo_id=photo_el.attrib['id'])
        for size in sizes_el.findall(".//size"):
            if size.attrib['label'] == 'Original':
                return ((int(size.attrib['width']), int(size.attrib['height'])), size.attrib['source'])
    except Exception, e:
        print e
    return ((-1, -1), '')

def delete_old_images():
    for filename in images_to_delete:
        if os.path.exists(filename):
            os.remove(filename)
            print 'removed file', filename

def delete_old_documents():
    for doc_id in documents_to_delete:
        if doc_id in db:
            db.delete(db[doc_id])
            print 'deleted ', doc_id
			
def flag_images_for_deletion():
    for filename in os.listdir(config.IMAGE_DIR):
        images_to_delete.append(os.path.join(config.IMAGE_DIR, filename))

def flag_documents_for_deletion():
    for doc in db.view('_design/religions/_view/religions'):
        documents_to_delete.append(doc.id)
		
def foo():
    before = datetime.datetime.now()
    christianity_passages = load_passages(filenames['Christianity'], 5)
    islam_passages = load_passages(filenames['Islam'])
    hinduism_passages = load_passages(filenames['Hinduism'])

    for i, p in enumerate(christianity_passages):
        matches = []
        max_sim, max_index = 0, 0
        before_passage = datetime.datetime.now()
        for ii, pp in enumerate(islam_passages):
            cosine.add_document(ii, ' '.join(pp))
            sim = cosine.classify_document(' '.join(p))
            if sim[ii] > max_sim:
                max_sim, max_index = sim[ii], ii
            cosine.clear()
        match = islam_passages[max_index]
        print datetime.datetime.now() - before_passage, i, max_sim, max_index
        print ' '.join(p)
        print ' '.join(match)
        matches.append(match)
        keywords = utils.get_common_words(' '.join(p), ' '.join(match))
        print keywords
        store_passage('Christianity', p, i, matches, keywords.keys(), 0, [])

    print 'DONE!', datetime.datetime.now() - before

def store_passage(religion, passage, passage_num, match_1, keywords, line_index, filenames):
    doc = {'religion':religion, 'passage':passage, 'passage_num':passage_num, 'matches':match_1, 'keywords':keywords, 'selected_line':line_index, 'images':filenames}
    couchdb_util.store_doc(db, doc)

def run_connections():
    flag_documents_for_deletion()
    foo()
    delete_old_documents()

def run_images():
    flag_images_for_deletion()
    load_images()
    delete_old_images()

if __name__ == '__main__':
    foo()
    #print replace_special_chars('&#363;&#363;&#255;a&#253; &#252;p &#252;p Cow &#220;&#217;dde&#216;r &#208;og&#199;&#224;ppl&#233;e&#203;&#209;')
    
    '''filename = filenames['Christianity'] 
    passages = load_passages(filename)
    count = 0
    for i, passage in enumerate(passages):
        if i == 0:
            after = datetime.datetime.now()
        count += 1
    print after - before
    print count'''
    
    '''for i, passage in enumerate(passages):
        for line in passage:
            print line'''
    '''text = simplejson.load(open(filename, 'r'))
    book = choose_random_book(text)
    verse = choose_random_verse(book)
    print verse'''
