import config
import random
import datetime
import simplejson
import couchdb
import flickrapi
import utils
import re

''' Passage length parameters '''
max_lines_per_passage = 9
max_chars_per_line = 25
max_passages = 1

''' Flickr search parameters '''
flickr_api_key = '0d5347d0ffb31395e887a63e0a543abe'
_flickr = flickrapi.FlickrAPI(flickr_api_key)
remove_all_stop_words = True
min_taken_date_filter = '946706400' #1/1/2000 #'1262325600' #1/1/2010
safe_search_filter = 1

''' Image parameters '''    
max_original_width, min_original_width = 3600, 1200
max_original_height, min_original_height = 2400, 800

''' Global properties '''
selected_images = []
db = couchdb.Server(config.COUCHDB_CONNECTION_STRING)['imagination']
filenames = {'Buddhism':'buddha.json', 'Christianity':config.OFFLINE_DIR + 'bible.json', 'Hinduism':config.OFFLINE_DIR + 'vedas.json', 'Islam':config.OFFLINE_DIR + 'quran.json'}

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

def load_passages(filename):
    text = simplejson.load(open(filename, 'r'))
    num_passages_yielded = 0
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
                        yield lines
                        num_passages_yielded += 1
                        #if num_passages_yielded >= max_passages:
                        #    return
                        lines = []
                    curr_line = [word]
                    char_count = 0

# NUMBER OF PASSAGES BY RELIGION:
# Christianity = 27,250    
# Islam = 3,080
# Hinduism = 4,723

def get_len(passages):
    count = 0
    for i, passage in enumerate(passages):
        if i == 0:
            after = datetime.datetime.now()
        count += 1
    return count

def load_images():
    for doc in db.view('_design/religions/_view/religions'):
        line_index = doc.value['selected_line']
        passage = doc.value['passage']
        line = passage[line_index]
        images = get_images_by_text(line, 3)
        print images
        print

def get_images_by_text(text, num_of_images):
    urls = []
    clean_line = replace_special_chars(text)
    clean_line = utils.strip_all_stop_words(clean_line)
    print clean_line
    count = 0
    try:
        for photo in _flickr.walk(text=clean_line, sort='interestingness-desc', content_type='1', min_taken_date=min_taken_date_filter, safe_search=safe_search_filter):
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
    sizes_el = _flickr.photos_getSizes(photo_id=photo_el.attrib['id'])
    for size in sizes_el.findall(".//size"):
        if size.attrib['label'] == 'Original':
            return ((int(size.attrib['width']), int(size.attrib['height'])), size.attrib['source'])
    return ((-1, -1), '')

def foo():
    before = datetime.datetime.now()
    christianity_passages = load_passages(filenames['Christianity']);
    islam_passages = load_passages(filenames['Islam']);
    hinduism_passages = load_passages(filenames['Hinduism']);

    count1 = 0
    count2 = 0
    total = 0
    for i, p in enumerate(christianity_passages):
        for ii, pp in enumerate(islam_passages):
            total += len(p) + len(pp)
        for ii, pp in enumerate(hinduism_passages):
            total += len(p) + len(pp)
            
            
    #print get_len(christianity_passages)
    #print get_len(islam_passages)
    #print get_len(hinduism_passages)
            
    print total
    after = datetime.datetime.now()
    print after - before

def replace_special_chars(text):
    ''' reference: http://www.webmonkey.com/2010/02/special_characters/ '''
    text = re.sub('&#(22[4-9]|257);', 'a', text)
    text = re.sub('&#(19[2-7]|256);', 'A', text)
    text = re.sub('&#231;', 'c', text)
    text = re.sub('&#199;', 'C', text)
    text = re.sub('&#208;', 'D', text)
    text = re.sub('&#(23[2-5]|275);', 'e', text)
    text = re.sub('&#(20[0-3]|274);', 'E', text)
    text = re.sub('&#7713;', 'g', text)
    text = re.sub('&#7712;', 'G', text)
    text = re.sub('&#(23[6-9]|299);', 'i', text)
    text = re.sub('&#(20[4-7]|298);', 'I', text)
    text = re.sub('&#241;', 'n', text)
    text = re.sub('&#209;', 'N', text)
    text = re.sub('&#(24[2-6]|333);', 'o', text)
    text = re.sub('&#(21[0-4]|216|332);', 'O', text)
    text = re.sub('&#(249|25[0-2]|363);', 'u', text)
    text = re.sub('&#(21[7-9]|220|362);', 'U', text)
    text = re.sub('&#(253|255|563);', 'y', text)
    text = re.sub('&#(221|562);', 'Y', text)
    return text

if __name__ == '__main__':
    load_images()    
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
