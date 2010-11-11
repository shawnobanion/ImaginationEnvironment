import urllib
import simplejson

SEARCH_BASE_IMAGES = 'http://ajax.googleapis.com/ajax/services/search/images'

def googleImageSearch(query,imgtype="default",imgsz='m',rsz='3',filetype='default',start=0,**kwargs):  
    """
    Performs a Google Search.

    @type query: C{string}
    @param query: the search string.
    @type size: C{string}
    @param size: the size of the search. Can be 'large' or 'small'.

    @rtype: C{dictionary}
    @return: the Google Image Search result set.
    """
    #print 'image query is %s' % query
    
    '''TODO: FIGURE OUT WHY RETURN AS_FILETYPE AS DEFAULT GIVES PROBLEMS'''
    result = {}

    kwargs.update({
        'v': 1.0,
        'q': query,
        'rsz': rsz,
        'safe':'active',
        'imgsz': imgsz,
        #'imgc':'color',
        'imgtype':imgtype,
		'start':start
    })
    
    if filetype == 'jpg':
        kwargs.update({'as_filetype':'jpg'})
    print kwargs
    url = SEARCH_BASE_IMAGES + '?' + urllib.urlencode(kwargs)
    result = simplejson.load(urllib.urlopen(url))
   
    return result

if __name__ == '__main__':
	ld = googleImageSearch('death', 'default', '2mp', 3, 'default', 0)
	for d in ld['responseData']['results']:
		for a, v in d.iteritems():
			print a, ":",  v
		break
		#print d['url']