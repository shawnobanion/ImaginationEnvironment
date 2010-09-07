import BeautifulSoup
import simplejson
import re

import utils as u

verse_start_regex = re.compile(r'^\s*\d+\.?(.*)')

def _scrape_chapter(html):
    ret = []
    doc = BeautifulSoup.BeautifulSoup(html)
    
    p = doc.find(text=re.compile('1. ')).parent #todo: find a better way to do this
    i = 2

    while p is not None:
        verse = ''
        while p is not None and not line_starts_with(p, str(i)):
            verse += ' ' + read_line(p)
            p = p.findNextSibling(True)
        ret.append(verse)
        i += 1

    return ret

def line_starts_with(p, exp):
    if p.string is None:
        return line_starts_with(p.contents[0], exp)
    return p.string.startswith(exp)

def read_line(p):
    line = ''
    
    if p.string is not None and p.string:
        words = re.sub('[0-9]*\. ', '', p.string) # remove '1.', '2.', etc.
        return words

    for i, text in enumerate(p):
        line += read_line(text)

    return line
                
def scrape_chapter(url):
    '''Takes a url like http://www.sacred-texts.com/hin/rigveda/rv05055.htm.
    Returns a list of strings, each a verse-ish'''
    return u.scrapeWith(url, _scrape_chapter)
    
def scrape_all_and_store():
    '''This is the main function to call.  It will scrape the whole page, and write out quran.json
    quran.json is a list of dictionaries.  Each dictionary has a 'book_name' and 'verses' keys.
    'verses' is a list of verses.'''
    root_url = 'http://www.sacred-texts.com/isl/yaq/yaq{0}.htm'
    filename = 'quran.json'
    quran = []
    for i in range(1, 10):
       index_url = root_url.format(str(i).zfill(3))
       print index_url
       chapter_name = 'foo'
       print 'Scraping #%s, %s...' % (i, chapter_name)
       verses = scrape_chapter(index_url)
       quran.append({'book_name':chapter_name, 'verses':verses})
       
    simplejson.dump(quran, open(filename, 'w'))

if __name__ == '__main__':
    scrape_all_and_store()
    #for i, verse in enumerate(scrape_chapter('http://www.sacred-texts.com/isl/yaq/yaq002.htm')):
     #   print i, verse
     
    print 'DONE!'
