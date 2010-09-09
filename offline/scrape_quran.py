import BeautifulSoup
import simplejson
import re

import utils as u

verse_start_regex = re.compile('p. [0-9]+')

def _scrape_chapter(html):
    ret = []
    doc = BeautifulSoup.BeautifulSoup(html)
    
    p = doc.find(text=re.compile('1. ')).parent #todo: find a better way to do this
    i = 2

    chapter_name = doc.body.h3.string

    while p is not None:
        verse = ''
        while p is not None and not line_starts_with(p, str(i)):
            line = read_line(p)
            match = verse_start_regex.match(line)
            if match is None:
                verse += ' ' + line
            p = p.findNextSibling('p')
        ret.append(verse)
        i += 1

    return chapter_name, ret

def line_starts_with(tag, exp):
    if tag.string is None:
        return line_starts_with(tag.contents[0], exp)
    return tag.string.startswith(exp)

def read_line(tag):
    line = ''
    if tag.string:
        words = re.sub('[0-9]+\. ', '', tag.string) # remove '1.', '2.', etc.
        return words
    for i, text in enumerate(tag):
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
    for i in range(1, 115):
       index_url = root_url.format(str(i).zfill(3))
       print index_url
       chapter_name, verses = scrape_chapter(index_url)
       print 'Scraping #%s, %s...' % (i, chapter_name)
       quran.append({'book_name':chapter_name, 'verses':verses})
       
    simplejson.dump(quran, open(filename, 'w'))

if __name__ == '__main__':
    scrape_all_and_store()
    #for i, verse in enumerate(scrape_chapter('http://www.sacred-texts.com/isl/yaq/yaq002.htm')):
    #    print i, verse
     
    print 'DONE!'
