import copy
import os
import random
import simplejson
import time
import couchdb
import flickrapi
import utils
import config
assert config.IMAGE_DIR, "You need to specify a directory to write images to in config.py"
assert os.path.isdir(config.IMAGE_DIR), "Your config.IMAGE_DIR does not specify a valid directory!"

''' Passage length parameters '''
max_lines_per_passage = 9
max_chars_per_line = 25
max_passages = 15

''' Flickr search parameters '''
flickr_api_key = '0d5347d0ffb31395e887a63e0a543abe'
_flickr = flickrapi.FlickrAPI(flickr_api_key)
remove_all_stop_words = True
min_taken_date_filter = '1262325600' #1/1/2010 '946706400' #1/1/2000
safe_search_filter = 1

''' Image parameters '''    
max_original_width, min_original_width = 3600, 1200
max_original_height, min_original_height = 2400, 800
default_image = 'http://infolab.northwestern.edu/media/uploaded_images/featured_illumination.jpg'

''' Global properties '''
selected_images = []
db = couchdb.Server('http://localhost:5984')['imagination'] # http://yorda.cs.northwestern.edu:5984/'
filenames = {'Buddhism':'buddha.json', 'Christianity':'bible.json', 'Hinduism':'vedas.json'}

''' Given a filename, this opens the file, enumerates through the books and versus to return the maximum allowed number of passages '''
def load_passages(filename):
    text = simplejson.load(open(filename, 'r'))
    num_passages_yielded = 0
    while True:
        book = choose_random_book(text)
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
                        yield lines
                        num_passages_yielded += 1
                        if num_passages_yielded >= max_passages:
                            return
                        lines = []
                    curr_line = [word]
                    char_count = 0


''' Selects a random book from the text and removes it from the list '''
def choose_random_book(text):
    index = random.randint(0, len(text) - 1)
    book = text[index]
    text.pop(index)
    return book

''' Selects a random number between 0 and the length of the string '''
def choose_line_index(passage):
    return random.randint(0, len(passage) - 1)

''' Gets the URL to the original version of the image, if it's available '''    
def _sizeAndURLOfImage(photo_el):
    sizes_el = _flickr.photos_getSizes(photo_id=photo_el.attrib['id'])
    for size in sizes_el.findall(".//size"):
        if size.attrib['label'] == 'Original':
            return ((int(size.attrib['width']), int(size.attrib['height'])), size.attrib['source'])
    return ((-1, -1), '')

def find_image(line):
    if remove_all_stop_words:
        clean_line = utils.strip_all_stop_words(line)
    else:
        clean_line = utils.sStripStopWords(line)
        
    try:
        i = 0
        for photo in _flickr.walk(text=clean_line, sort='interestingness-desc', per_page='20', content_type='1', min_taken_date=min_taken_date_filter, safe_search=safe_search_filter):
            (width, height), url = _sizeAndURLOfImage(photo)
            i+=1
            if url:
                photo_id = photo.attrib['id']
                #we have a max here, because my network or PIL doesn't like 11k by 8k pictures
                #if not photo_id in selected_images and max_original_width > width > min_original_width and max_original_height > height > min_original_height:
                if not photo_id in selected_images and width > min_original_width and height > min_original_height:
                    print i, '/ 20', clean_line
                    print url
                    print
                    selected_images.append(photo_id)
                    return url
    except Exception, e:
            print 'An error occurred while performing a flickr API search', e
    return ''

''' Saves 3 copies of the image to the local directory and persists the record to the db '''
def store_passage(religion, passage, passage_num, line_index, image_url):
    # set defaults if no image was found
    if line_index == '':
        line_index = -1
    if not image_url:
        image_url = default_image
        
    file_ending = image_url.rpartition('.')[-1]
    out_filenames = ['%s_%s.%s' % (int(time.time() * 1000), i, file_ending) for i in range(3)]
    # saves three copies of the image to the stored_images directory
    utils.crop_images(image_url, *[os.path.join(config.IMAGE_DIR, f) for f in out_filenames])
    # persists the record to the db
    record = {'religion':religion, 'passage':passage, 'passage_num':passage_num, 'selected_line':line_index, 'images':out_filenames}
    try:
        db.save(record)
    except Exception, e:
        print 'An error occurred while saving the record to the db, trying again...'
        db.save(record)

''' Given a passage, this randomly selects a line from the passage and returns the line index and image url '''
def run_passage(passage):
    for verse in passage:
        print verse
    print
    destructable_passage = copy.copy(passage)
    while True: # infinite loop
        line_index = choose_line_index(destructable_passage)
        image_url = find_image(destructable_passage[line_index])
        if not image_url:
            del[destructable_passage[line_index]]
            if not destructable_passage:
                return ('', '')
            continue
        break # break the infinite loop if I have a valid image_url
    return (line_index, image_url)

''' Given a religion name (e.g. filename) this loads the passages, finds an image, and stores the results in the db '''
def run(religion):
    filename = filenames[religion]
    passages = load_passages(filename)
    for passage_num, passage in enumerate(passages):
        line_index, image_url = run_passage(passage)
        store_passage(religion, passage, passage_num, line_index, image_url)

            
''' Deletes all passages from the db while preserving any views you may have '''
def delete_passages():
    for doc_id in db:
        if not doc_id.startswith('_design'): # do not delete any views we have saved!
            db.delete(db[doc_id])
            print 'deleted ' + doc_id
    for filename in os.listdir(config.IMAGE_DIR):
        os.remove(os.path.join(config.IMAGE_DIR, filename))
                                
if __name__ == '__main__':
    delete_passages()
    run('Christianity')
    run('Buddhism')
    run('Hinduism');
    #for doc in db.view('_design/religions/_view/religions', key=["Christianity", 5]):#, endkey=["Christianity", 10000000]):
    #    print doc
    print 'DONE!'
    
