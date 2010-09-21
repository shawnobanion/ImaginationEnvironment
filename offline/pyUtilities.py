'''This is a collection of utility functions that are convenient throughout News at Seven
or are conceivably convenient in other projects.'''
import urllib, os, socket, sys
sFakeUserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.8.1.3) Gecko/20070309 Firefox/2.0.0.3'
urllib.FancyURLopener.version = sFakeUserAgent
from xml.sax.saxutils import unescape, escape
from urllib import quote
import time, random
import pickle
import threading
import atexit
import copy
import re
try:
    import hashlib
    md5 = hashlib.md5
except ImportError:
    import md5
    md5 = md5.new
import unicodedata
from os import popen,system
import urllib2
from BeautifulSoup import BeautifulSoup

from config import *

LastHitLock = threading.Lock()

sLocalhostName = socket.gethostname()
sPathJoin = os.path.join
ssPathSplit = os.path.split

_markup_regexes = [re.compile('<!--.*?-->', re.IGNORECASE | re.S), re.compile(r'<\s*script.*?</\s*script\s*>', re.IGNORECASE | re.S), re.compile('<[^>]*>', re.IGNORECASE | re.S)]
_space_regex = re.compile(r'\s{2,}', re.S) #do a _space_regex.sub('  ', text) to collapse more-than-two-spaces down to two-spaces

#import logging.config
#logging.config.fileConfig(sPathJoin(NEWS_AT_SEVEN_DIR, 'logging.conf'))

#__logger = logging.getLogger('shared')

ISA_SERVER, ISA_PORT = 'localhost', 6886  #not currently used.

NORMAL_SPLIT, CELEBRITY_SPLIT, NO_SPLIT = range(3)

HEAD_TURN, HEAD_BODY_TURN, HEAD_BODY_LEGS_TURN = range(3)

TIME_BETWEEN_HITS = {}
TIME_BETWEEN_HITS['http://news.yahoo.com'] = 10
TIME_BETWEEN_HITS['http://en.wikipedia.org'] = 5
TIME_BETWEEN_HITS['default'] = 1
LAST_HITS = {}

__bDebug = False

liTime = time.localtime()
sDateString = '%s-%s-%s' % (liTime[1], liTime[2], liTime[0]) #This is useful for naming files with dates, etc.  Format is mM-dD-YYYY

_hOriginalOutput = sys.stdout

def stripExtraSpaces(text):
    """
    Ensures that there is only one space between words.
    
    @type text: C{string}
    @param text: a string with multiple spaces between words.
    
    @rtype: C{string}
    @return: the string with only one space between words.
    """

    oldLen = len(text)
    newLen = -1
    while newLen != oldLen:
        oldLen = len(text)
        text = text.replace('  ',' ')
        newLen = len(text)
    return text


def dayOfWeek(date):
	dayofWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	return dayofWeek[date.weekday()]

preps = ['about','above','across','after','against','around','at','before','behind','below','beneath','beside','besides','between','beyone','by','down','during','except','for','from','in','inside','into','like','near','of','off','on','out','outside','over','since','through','throughout','till','to','toward','under','until','up','upon','with','without']

def bIsPreposition(word):
	if word.lower().strip() in preps:
		return True
	else:
		return False


def removePunctuation(text, spaces = True,lsExcept=[]):
        """
        Removes punctuation from a string.

        @type text: C{string}
        @param text: a string with punctuation.

        @rtype: C{string}
        @return: the string without punctuation.
        """

        spacePunctuation = ["'",'-','_','=','+','/','\\']
        noSpacePunctuation = ['.','?','!',',',':',';','(',')','[',']','{','}','@','#','$','%','^','&','*','"']

        if spaces:
            for punct in spacePunctuation:
                if punct not in lsExcept:
                    text = text.replace(punct,' ')
        else:
            for punct in spacePunctuation:
                if punct not in lsExcept:
                    text = text.replace(punct,'')
        for punct in noSpacePunctuation:
            if punct not in lsExcept:
                text = text.replace(punct,'')

        return stripExtraSpaces(text.strip(' '))


def numberMonth(strMonth):
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    
    for index,month in enumerate(months):
        if month.find(strMonth) > -1:
            #print strMonth
            return index+1
            
    return -1

def cleanBeautifulSoup(contents):
    firstQuote = True
    lsReturn = []
    for tag in contents:
         if tag.string and len(tag.string.strip()) > 0:
             if tag.string.strip()[0] == '"' and firstQuote:
                 firstQuote = False
             elif tag.string.strip()[0] == '"' and not firstQuote:
                 lsReturn[-1] = '"' + lsReturn[-1] + '"'
                 firstQuote = True
             elif tag.string.strip()[0] in '.,;:':
                 lsReturn[-1] += tag.string
             else:
                 lsReturn.append(toascii(tag.string).strip())

    summary = ' '.join([content for content in lsReturn])
    reU = re.compile('\(.*?\)')
    summary = reU.sub('',summary)
    summary = ' '.join([word.strip() for word in summary.split()])
    return summary

code_to_state = {"WA": "WASHINGTON", "VA": "VIRGINIA", "DE": "DELAWARE", "DC": "DISTRICT OF COLUMBIA", "WI": "WISCONSIN", "WV": "WEST VIRGINIA", "HI": "HAWAII", "AE": "Armed Forces Middle East", "FL": "FLORIDA", "FM": "FEDERATED STATES OF MICRONESIA", "WY": "WYOMING", "NH": "NEW HAMPSHIRE", "NJ": "NEW JERSEY", "NM": "NEW MEXICO", "TX": "TEXAS", "LA": "LOUISIANA", "NC": "NORTH CAROLINA", "ND": "NORTH DAKOTA", "NE": "NEBRASKA", "TN": "TENNESSEE", "NY": "NEW YORK", "PA": "PENNSYLVANIA", "CA": "CALIFORNIA", "NV": "NEVADA", "AA": "Armed Forces Americas", "PW": "PALAU", "GU": "GUAM", "CO": "COLORADO", "VI": "VIRGIN ISLANDS", "AK": "ALASKA", "AL": "ALABAMA", "AP": "Armed Forces Pacific", "AS": "AMERICAN SAMOA", "AR": "ARKANSAS", "VT": "VERMONT", "IL": "ILLINOIS", "GA": "GEORGIA", "IN": "INDIANA", "IA": "IOWA", "OK": "OKLAHOMA", "AZ": "ARIZONA", "ID": "IDAHO", "CT": "CONNECTICUT", "ME": "MAINE", "MD": "MARYLAND", "MA": "MASSACHUSETTS", "OH": "OHIO", "UT": "UTAH", "MO": "MISSOURI", "MN": "MINNESOTA", "MI": "MICHIGAN", "MH": "MARSHALL ISLANDS", "RI": "RHODE ISLAND", "KS": "KANSAS", "MT": "MONTANA", "MP": "NORTHERN MARIANA ISLANDS", "MS": "MISSISSIPPI", "PR": "PUERTO RICO", "SC": "SOUTH CAROLINA", "KY": "KENTUCKY", "OR": "OREGON", "SD": "SOUTH DAKOTA"}

def getStateName(abbrev):
    abbrev = abbrev.upper()
    try:
        return code_to_state[abbrev]
    except KeyError:
        return None

state_to_code = {'VERMONT': 'VT', 'GEORGIA': 'GA', 'IOWA': 'IA', 'GUAM': 'GU', 'KANSAS': 'KS', 'FLORIDA': 'FL', 'VIRGINIA': 'VA', 'NORTH CAROLINA': 'NC', 'ALASKA': 'AK', 'NEW YORK': 'NY', 'CALIFORNIA': 'CA', 'ALABAMA': 'AL', 'TEXAS': 'TX', 'FEDERATED STATES OF MICRONESIA': 'FM', 'IDAHO': 'ID', 'Armed Forces Americas': 'AA', 'DELAWARE': 'DE', 'HAWAII': 'HI', 'ILLINOIS': 'IL', 'CONNECTICUT': 'CT', 'DISTRICT OF COLUMBIA': 'DC', 'MISSOURI': 'MO', 'NEW MEXICO': 'NM', 'PUERTO RICO': 'PR', 'OHIO': 'OH', 'MARYLAND': 'MD', 'ARKANSAS': 'AR', 'MASSACHUSETTS': 'MA', 'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'PALAU': 'PW', 'COLORADO': 'CO', 'Armed Forces Middle East': 'AE', 'NEW JERSEY': 'NJ', 'UTAH': 'UT', 'MICHIGAN': 'MI', 'WYOMING': 'WY', 'WASHINGTON': 'WA', 'MINNESOTA': 'MN', 'OREGON': 'OR', 'AMERICAN SAMOA': 'AS', 'VIRGIN ISLANDS': 'VI', 'MARSHALL ISLANDS': 'MH', 'Armed Forces Pacific': 'AP', 'SOUTH CAROLINA': 'SC', 'INDIANA': 'IN', 'NEVADA': 'NV', 'LOUISIANA': 'LA', 'NORTHERN MARIANA ISLANDS': 'MP', 'ARIZONA': 'AZ', 'WISCONSIN': 'WI', 'NORTH DAKOTA': 'ND', 'MONTANA': 'MT', 'PENNSYLVANIA': 'PA', 'OKLAHOMA': 'OK', 'KENTUCKY': 'KY', 'RHODE ISLAND': 'RI', 'MISSISSIPPI': 'MS', 'NEBRASKA': 'NE', 'NEW HAMPSHIRE': 'NH', 'WEST VIRGINIA': 'WV', 'MAINE': 'ME'}

def getStateAbbrev(stateName):
    stateName = stateName.upper()
    try:
        return state_to_code[stateName]
    except KeyError:
        return None


class DummyObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class __cIHateUnicode:
    def __init__(self, d):
        self.d = d
    def __getitem__(self, iKey):
        if iKey in self.d:
            return self.d[iKey]
        if iKey > 128:
            return unichr(iKey)
        return chr(iKey)
    def __call__(self, iKey):
        return self.__getitem__(iKey)

cCharMap = __cIHateUnicode({233:'e'})

class ThreadSafeCounter:
    import threading
    def __init__(self):
        self.__iValue = 0
        self.__cLock = threading.Semaphore()
    def Increment(self, iIncrement=1):
        self.__cLock.acquire(True)
        self.__iValue += iIncrement
        self.__cLock.release()
        return self
    def Decrement(self, iDecrement=1):
        self.__cLock.acquire(True)
        self.__iValue -= iDecrement
        self.__cLock.release()
        return self
    @property
    def value(self):
        self.__cLock.acquire(True)
        iRet = self.__iValue
        self.__cLock.release()
        return iRet
    def __iadd__(self, iIncrement):
        return self.Increment(iIncrement)
    def __isub__(self, iDecrement):
        return self.Decrement(iDecrement)
    def __int__(self):
        return self.value
    
class CachedAccess:
    def __init__(self, func, size):
        self._cache = {}
        self._size = size
        self._func = func
        self._lock = threading.Lock()
    def __getitem__(self, key):
        self._lock.acquire()
        if key in self._cache:
            ret = self._cache[key]
        else:
            ret = self._func(key)
            self._cache[key] = ret
            if len(self._cache) > self._size:
                del self._cache
        self._lock.release()
        return ret
    
class SettableGenerator(object):
    def __init__(self, gen):
        self._gen = gen
        self._l = []
        self._use_l = False
    def __getitem__(self, k):
        return self._l[k]
    def __setitem__(self, k, v):
        self._l[k] = v
    def __deepcopy__(self, memo):
        import copy
        ret = SettableGenerator(self._gen)
        ret._l = copy.deepcopy(self._l)
        ret._use_l = self._use_l
        return ret
    def __copy__(self):
        import copy
        ret = SettableGenerator(self._gen)
        ret._l = copy.copy(self._l)
        ret._use_l = self._use_l
        return ret
    def _der(self):
        for p in self._gen:
            self._l.append(p)
            yield p
        self._use_l = True
    def __iter__(self):
        if self._use_l:
            return self._l.__iter__()
        else:
            return self._der()
    def __str__(self):
        ret = 'Settable Generator with %s settable items' % (len(self._l))
        return ret
    def __repr__(self):
        return str(self)

#l = SettableGenerator(xrange(5))
#for p in l:
#    print p
#for p in l:
#    print p
#l[0] = 42
#for p in l:
#    print p
_char_map = {8722: '-', 8211: '-', 8212: '-', 8213: '-', 8216: "'", 8217: "'", 8218: ',', 8220: '"', 8221: '"', 8230: '...', 187: '>>', 7789: 't', 171: '<<', 173: '-', 180: "'", 699: "'", 7871: 'e', 192: 'A', 193: 'A', 194: 'A', 195: 'A', 196: 'A', 197: 'A', 198: 'Ae', 199: 'C', 200: 'E', 201: 'E', 202: 'E', 203: 'E', 204: 'I', 7885: 'o', 206: 'I', 205: 'I', 208: 'D', 209: 'N', 210: 'O', 211: 'O', 212: 'O', 213: 'O', 214: 'O', 215: 'x', 216: 'O', 217: 'U', 218: 'U', 207: 'I', 220: 'U', 221: 'Y', 223: 'S', 224: 'a', 225: 'a', 226: 'a', 227: 'a', 228: 'a', 229: 'a', 230: 'ae', 231: 'c', 232: 'e', 233: 'e', 234: 'e', 235: 'e', 236: 'i', 237: 'i', 238: 'i', 239: 'i', 240: 'o', 241: 'n', 242: 'o', 243: 'o', 244: 'o', 245: 'o', 246: 'o', 247: '/', 248: 'o', 249: 'u', 250: 'u', 251: 'u', 252: 'u', 253: 'y', 255: 'y', 256: 'A', 257: 'a', 259: 'a', 261: 'a', 263: 'c', 268: 'C', 269: 'c', 279: 'e', 281: 'e', 283: 'e', 287: 'g', 219: 'U', 298: 'I', 299: 'i', 304: 'I', 305: 'i', 322: 'l', 324: 'n', 332: 'O', 333: 'o', 335: 't', 337: 'o', 339: 'oe', 345: 'r', 346: 'S', 347: 's', 351: 's', 352: 'S', 353: 's', 355: 'c', 363: 'u', 367: 'u', 378: 'z', 379: 'Z', 381: 'Z', 382: 'z', 924: 'M', 451: '!'}
def toascii(text):
    if type(text) is not unicode:
        try:
            text = unicode(text, "utf-8", 'ignore')
        except TypeError, e:
            pass
        text = unicodedata.normalize('NFKD', text)
    ret = [c if ord(c) < 128 else _char_map.get(ord(c), '') for c in text]
    ret = ''.join(ret)
    return ret    
        
def dump_dict(d):
    '''Returns a string representation of a dict that you can hash off of.  dump_dict(d1) == dump_dict(d2) if d1 == d2'''
    ret = ','.join(['key(%s)=value(%s)' % (k, v) for k, v in sorted(d.items())])
    return ret 

def flatten(lists):
    ret = []
    for l in lists:
        if hasattr(l, '__iter__') and not isinstance(l, basestring):
            ret.extend(l)
        else:
            ret.append(l)
    return ret
 
def wordDifficulty(word,corpus=None): 
    """You can now hit the speech server like this:"""
    """http://yorda.cs.northwestern.edu:8080/get_difficulty?word=jiahui"""
    """And get back a difficulty score of how hard it is to say."""  
    """nate is 0, jiahui is 2, Mxyzptlk is 4.0, and the is -4617.41666666667.""" 
    if not corpus:
        sURL = 'http://yorda.cs.northwestern.edu:8081/get_difficulty?word=%s' % word
    else:
        sURL = 'http://yorda.cs.northwestern.edu:8081/get_difficulty?word=%s&corpus=%s' % (word,corpus)
    myUrlclass = urllib.FancyURLopener()
    return float(__getFile(myUrlclass.open, sURL ))



__dATOI = {}
__iATOI = 0
__dITOA = {}
def atoi(s):
    '''NOT AT ALL WHAT YOU'D EXPECT!  THIS IS A TERRIBLE NAME, BUT I JUST COULDN'T HELP MYSELF!'''
    if type(s) == int:
        return s
    global __iATOI
    if s in __dATOI:
        return __dATOI[s]
    else:
        __dATOI[s] = __iATOI
        __dITOA[__iATOI] = s
        __iATOI += 1
        return __iATOI - 1

def itoa(i):
    '''NOT AT ALL WHAT YOU'D EXPECT!  THIS IS A TERRIBLE NAME, BUT I JUST COULDN'T HELP MYSELF!'''
    if type(i) == str:
        return i
    return __dITOA[i]

__iLastUniqueID = -1
__cUniqueLock = threading.Lock()

def iUniqueID():
    '''Guaranteed to be unique, threadsafe, etc.'''
    global __iLastUniqueID
    __cUniqueLock.acquire()
    iRet = int(time.time() * 1000)
    if iRet <= __iLastUniqueID:
        iRet = __iLastUniqueID + 1
    __iLastUniqueID = iRet
    __cUniqueLock.release()
    return iRet

def guess_val(text):
    '''Takes a string and tries to guess what type the user meant.  So if text is "4", they probably meant the int 4,
    if it's "foo, bar, baz" they probably meant ['foo', 'bar', 'baz'], etc.  It's not perfect, but a reasonable guess.'''
    if text.lower() == 'none':
        return None
    if text.lower() == '[]':
        return []
    if text.lower() == '{}':
        return {}
    try:
        ret = int(text)
        return ret
    except ValueError:
        pass
    try:
        ret = float(text)
        return ret
    except ValueError:
        pass
    if text and text.count(',') / float(len(text)) > .05 or text.endswith(','):
        ret = [s.strip() for s in text.split(',') if s.split()]
        return ret
    return text

class StackedDict:
    '''An easy way to represent scopes of variables.  It's really a list of dicts, so if the key isn't
    found in the first dict, it checks the second, etc.  Setting a key always does it in the nearest
    scope/dict.'''
    def __init__(self):
        self._ld = []
    def push(self, d=None):
        if d is None:
            d = {}
        self._ld.insert(0, d)
    def pop(self):
        return self._ld.pop(0)
    def __getitem__(self, k):
        for d in self._ld:
            if k in d:
                return d[k]
        raise KeyError
    def __contains__(self, k):
        try:
            foo = self[k]
        except KeyError:
            return False
        return True
    def __setitem__(self, k, v):
        self._ld[0][k] = v
    def __str__(self):
        ret = '<%s>' % (', '.join([str(d) for d in self._ld]))
        return ret
    def __repr__(self):
        return str(self)

def EZGen(val):
    '''If you don't have the copy.copy in there you get some really subtle errors.  Believe me!'''
    while True:
        yield copy.copy(val)

def any(lx):
    for x in l:
        if x:
            return x
    return False

def weighted_string(*args):
    '''Takes something like weighted_string(2, 'Nate', 'Dogg') and "weights" 'Nate' twice as much as Dogg.  Format is pairs weight, string, weight, string...
    but if you leave off the weight, it's assumed to be one.  Just returns a repeated string, but works fine.  So if you have a dictionary with title and body
    keys, and want to weight the title x2 for counting or tfidf or something, you could do 
    content = weighted_string(2, d['title'], d['body'])'''
    ret = []
    i = 0
    while i < len(args):
        if type(args[i]) is int:
            for j in range(args[i]):
                ret.append(args[i+1])
            i += 1
        elif type(args[i]) is str or type(args[i]) is unicode:
            ret.append(args[i])
        else:
            assert 0, 'weighted_string only takes ints and strings!'
        i += 1
    ret = ' '.join(ret)
    return ret
    
def bLooseIn(sLHS, sRHS):
    '''bLooseIn('Hillary Clinton', 'Hillary Rodham Clinton') -> True
    bLooseIn('Hillary Clinton', 'My name is Hillary.  Is yours Clinton?') -> True
    bLooseIn('Hillary Clinton', 'Clinton Hillary') -> True
    bLooseIn('Hillary Clinton', 'Hillary foo bar') -> False'''
    for sWord in sLHS.split():
        if sWord not in sRHS:
            return False
    return True

def bLooseStringEquals(lhs, rhs):
    lhs, rhs = sStripStopWords(lhs).lower().strip(), sStripStopWords(rhs).lower().strip()
    return lhs == rhs
    
def iMultiStringCount(sStr, lsTerms):
    '''Returns the total number of occurrences of the terms in lsterms in sStr.  Is smart about 
    iMultiStringCount('foobar baz', ['foobar', 'bar']) -> 1 and not 2.'''
    dCounts = {}
    for sTerm in lsTerms:
        dCounts[sTerm] = sStr.count(sTerm)
    #so far so good, now we need to take out extras ('Bush' and 'George Bush' getting points for 'George Bush')
    dPartOf = {}
    for sTerm in lsTerms:
        dPartOf[sTerm] = []
        for s in lsTerms:
            if sTerm in s and sTerm != s:
                dPartOf[sTerm].append(s)
    for sTerm in dCounts:
        for sBigger in dPartOf[sTerm]:
            dCounts[sTerm] -= dCounts[sBigger]
    
    iRet = sum(dCounts.values())
    return iRet

class Borg(object):
    '''Taken right from Python Cookbook, look up the Borg design pattern.  In general, I think design patterns are overblown, but this one seems nice.
    Besides, I've always wondered how the hell __new__ works.'''
    _shared_state = {}
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared_state
        return obj

class Singleton(object):
    '''Also taken from the Python Cookbook.  Thanks Google Booksearch!'''
    def __new__(cls, *args, **kwargs):
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls, *args, **kwargs)
        return cls._inst
    
def lxEverythingInModulesThat(lsModules, funcTest):
    for sModule in lsModules:
        exec('import %s' % sModule)
    
    lxRet = []
    for sModule in lsModules:
        for s in dir(locals()[sModule]):
            if funcTest(getattr(locals()[sModule], s)):
                lxRet.append(getattr(locals()[sModule], s))
    return lxRet

class cPrintEverythingMixin:
    def __str__(self):
        sRet = ''
        sRet = '\n'.join(['%s ==> %s' % (k, v) for (k, v) in self.__dict__.items()])
        return sRet
    
class BlankObject:
    pass

class DefaultDict(dict):
    """Dictionary with a default value for unknown keys, from Peter Norvig"""
    def __init__(self, default):
        self.default = default

    def __getitem__(self, key):
        if key in self: 
            return self.get(key)
        else:
            ## Need copy in case self.default is something like []
            return self.setdefault(key, copy.deepcopy(self.default))

    def __copy__(self):
        copy = DefaultDict(self.default)
        copy.update(self)
        return copy

class MaxSizeCache:
    '''A Dictionary with a maximum size.   If you try and add more entries than iMaxEntries, it will drop the last used one.
    Thread-safe.  The last-used is only as accurate as the system clock'''
    def __init__(self, iMaxEntries):
        assert iMaxEntries, 'Why would you want a zero-sized cache?!'
        self.__iMaxEntries = iMaxEntries
        self.__dLastUsed = {}
        self.__dEntries = {}
        self.__cLock = threading.Lock()
    def __addEntry(self, k, v):
        self.__dEntries[k] = v
        self.__dLastUsed[k] = time.time()
    def __delLastUsed(self):
        fMin = time.time()
        kMin = None
        for k, v in self.__dLastUsed.items():
            if v < fMin:
                fMin = v
                kMin = k
        del self.__dEntries[kMin]
        del self.__dLastUsed[kMin]
    def __setitem__(self, kNew, vNew):
        self.__cLock.acquire()
        if kNew in self.__dEntries or len(self.__dEntries) < self.__iMaxEntries:
            self.__addEntry(kNew, vNew)
        else:
            self.__delLastUsed()
            self.__addEntry(kNew, vNew)
        self.__cLock.release()
    def __getitem__(self, k):
        self.__cLock.acquire()
        xRet = self.__dEntries[k]
        self.__dLastUsed[k] = time.time()
        self.__cLock.release()
        return xRet
    def __delitem__(self, k):
        self.__cLock.acquire()
        del self.__dEntries[k]
        del self.__dLastUsed[k]
        self.__cLock.release()
    def __getattr__(self, k):
        self.__cLock.acquire()
        xRet = getattr(self.__dEntries, k)
        self.__cLock.release()
        return xRet
        

def sLooseMD5Hash(sText):
    '''This is intended to return a "loose hash" that will be the same with slightly different text.  If Yahoo! fixes a mispelling, for example, we 
    don't want to rerun the story.
    The algorithm is from Sanj, do a histogram of all the words, take the top half, and make a string and hash that.  It makes sense,
    we'll see how it works.  My hunch is its too lenient on short texts.'''
    dCounts = DefaultDict(0)
    sText = sScrubString(sText, True)
    for sWord in sText.split():
        dCounts[sWord] += 1
    llSorted = sorted(dCounts.items(), lambda x, y: -cmp(x[1], y[1]))
    lsTopWords = [k for (k, v) in llSorted[:len(llSorted)/2]]
    sRet = md5(' '.join(lsTopWords)).hexdigest()
    return sRet



def In(xTest, lx, func):
    '''Similar to x in lx, but tests with func.'''
    for x in lx:
        if func(xTest, x):
            return True
    return False

  

def sXMLUnescape(s):
    '''Use this.  Thanks for nothing, saxutils.'''
    sRet = unescape(s, {'&nbsp;':' ','&ndash;':'-','&quot;': '"', '&apos;': "'", '&#151;':',', '&#39;':"'", '&#151;':'-', '&#36;':'$','&#8217;':"'",'&#8220;':'"','&#8221;':'"','&#8212;':'-'})
    reU = re.compile('&.*?;')
    sRet = re.sub(reU,'',sRet)
    return sRet



def sXMLEscape(s):
    '''Use this.  Thanks for nothing, saxutils.'''
    
    sRet = escape(s, {'"':'&quot;', "'":'&apos;', ',':'&#151;', '-':'&#151;', '$':'&#36;'})
    return sRet

#stuff = sXMLEscape('"yep"')
#print stuff
#print sXMLEscape(stuff)

def iStringDistance(a,b):
    '''Calculates the Levenshtein distance between a and b.
    from hetland.org'''
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]

def iListDistance(a, b):
    #shew!
    return iStringDistance(a, b)

def iMaxIndex(lx):
    '''max() returns the max() value, this returns the index of the max() value.  Tie breaker goes to the
    first.'''
    if not lx:
        return -1
    xMaxVal, iMaxIndex = lx[0], 0
    for i, x in enumerate(lx):
        if x > xMaxVal:
            xMaxVal = x
            iMaxIndex = i
    return iMaxIndex

def max_gen(iter_, n):
    '''Takes an iterator or generator or list or whatever, and an int, n.  It will only yield the first n elements
    from iter_.  Pass in a negative value for n and it will run forever.'''
    for i, val in enumerate(iter_):
        if i == n:
            return
        yield val

def sSharedPrefix(sLHS, sRHS, iLHSOffset=0, iRHSOffset=0):
    '''Returns a string that has all that sLHS and sRHS start with in common.
    sSharedPrefix("NateNichols", "NateBillingsworth")->"Nate".'''
    i = 0
    while i+iLHSOffset < len(sLHS) and i+iRHSOffset < len(sRHS) and sLHS[i+iLHSOffset] == sRHS[i+iRHSOffset]:
        i += 1
    ret = sLHS[iLHSOffset:i+iLHSOffset]
    return ret

def convertMoney(sStr):
   '''This converts $399.95 to 399 dollars and 95 cents'''
   
   cMatch = re.compile(r'\$\s*(?P<dollars>\d+)\.(?P<cents>\d\d)')
   
   sText = cMatch.sub('\g<dollars> dollars and \g<cents> cents', sStr)
   return sText

def convertThousands(sText):
    
    
    #tests for 2300,2400,2500,etc, and also at different
    #positions in the sentence (beginning, middle or end)
    cMatch = re.compile(r'(?P<begin>\D)(?P<num1>\d[1-9])00(?P<end>\D)')
    sText = cMatch.sub(r' \g<begin>\g<num1> hundred \g<end> ',sText)
    cMatch = re.compile(r'(?P<begin>\D)(?P<num1>\d[1-9])00($)')
    sText = cMatch.sub(r' \g<begin>\g<num1> hundred ',sText)
    cMatch = re.compile(r'(^)(?P<num1>\d[1-9])00(?P<end>\D)')
    sText = cMatch.sub(r' \g<num1> hundred \g<end> ',sText)
    cMatch = re.compile(r'(^)(?P<num1>\d[1-9])00($)')
    sText = cMatch.sub(r' \g<num1> hundred ',sText)
    
    #tests for last two digits as a single digit # 1-9 ,etc, and also at different
    #positions in the sentence (beginning, middle or end)
    cMatch = re.compile(r'(?P<begin>\D)(?P<num1>\d[1-9])0(?P<num2>[1-9])(?P<end>\D)')
    sText = cMatch.sub(' \g<begin>\g<num1> hundred and \g<num2> \g<end> ',sText)
    cMatch = re.compile(r'(?P<begin>\D)(?P<num1>\d[1-9])0(?P<num2>[1-9])($)')
    sText = cMatch.sub(' \g<begin>\g<num1> hundred and \g<num2> ',sText)
    cMatch = re.compile(r'(^)(?P<num1>\d[1-9])0(?P<num2>[1-9])(?P<end>\D)')
    sText = cMatch.sub(' \g<num1> hundred and \g<num2> \g<end>',sText) 
    cMatch = re.compile(r'(^)(?P<num1>\d[1-9])0(?P<num2>[1-9])($)')
    sText = cMatch.sub(' \g<num1> hundred and \g<num2> ',sText)
      
    #tests for last two digits as a double digit 10-99 ,etc, and also at different
    #positions in the sentence (beginning, middle or end)
    cMatch = re.compile(r'(?P<begin>\D)(?P<num1>\d[1-9])(?P<num2>[0-9][0-9])(?P<end>\D)')
    sText = cMatch.sub(' \g<begin> \g<num1> hundred \g<num2> \g<end>',sText)
    cMatch = re.compile(r'(?P<begin>\D)(?P<num1>\d[1-9])(?P<num2>[0-9][0-9])($)')
    sText = cMatch.sub(' \g<begin> \g<num1> hundred \g<num2> ',sText)
    cMatch = re.compile(r'(^)(?P<num1>\d[1-9])(?P<num2>[0-9][0-9])(?P<end>\D)')
    sText = cMatch.sub(' \g<num1> hundred \g<num2>\g<end> ',sText) 
    cMatch = re.compile(r'(^)(?P<num1>\d[1-9])(?P<num2>[0-9][0-9])($)')
    sText = cMatch.sub('\g<num1> hundred \g<num2> ',sText)
    
    return sText

def storyIncomprehensible(sStr):
    
    cMatch = re.compile(r'(([A-Z]+[0-9]+)|([0-9]+[A-Z]+))')
    cMatch2 = re.compile(r'\s+')
    
    lList = cMatch.findall(sStr)
    lList2 = cMatch2.findall(sStr)
    
    if len(lList) > 0:
        num1 = float(len(lList))
        num2 = float(len(lList2))
        
        #if 10% or more of the words are something
        #like A200, 2GHZ, and so on get rid of
        #story
        #print num1/num2
        if num1/num2 >= .1:
            return "true"
        
    return "false"   

def sumAny(*args):
    '''Like sum, but works for anything.  THis is probably already provided but I don't know what it would becalled.'''
    assert 0, "Don't use this, use sum instead.  You can use sum on lists and stuff if you provide an appropriate start value (the second arg)"
    ret = args[0]
    for x in args[1:]:
        ret = ret + x
    return ret
 
def tStoreFileLocally(sURL, sHostname='', iPort=8080, sSuffix=None,sFileName = '',bImage=False,sPath=''):
    '''Takes a path to a remote resource (like an image) and stores a copy of that locally in your www directory with a random unique name.
    Returns a tuple, the first element is a local path ('c:\www\foo.jpg'), the second is a url ('http://yourcomputername/foo.jpg').
    The URL is generated by socket.getfqdn() and adds in the iPort.  If you specify a different sHostname, you will also need to specify a port (if it's not 80.)
    and the http:// part.
    If you pass in any string (including the empty one) for the suffix, that will be the suffix on the file, else the function will try and guess it from the url.'''
    #print "tStoreFile bImage %s" % bImage
    
    if sPath == '':
        sPath = sPathJoin(WWW_DIR, 'CachedImages')
    
    
    if not os.path.exists(sPath):
        os.mkdir(sPath)
    
    if sFileName == '':
        sFileName = md5(str(random.random())).hexdigest()
    
    if sSuffix == None:
        sSuffix = '.' + sURL.split('.')[-1]
    if sHostname:
        sLocalURL = sHostname.strip('/') + '/CachedImages/' + sFileName+sSuffix
    else:
        sLocalURL = 'http://%s:%s/CachedImages/%s' % (socket.getfqdn(), iPort, sFileName+sSuffix)
    
    
    sFileName = sPathJoin(sPath, sFileName+sSuffix)
    kwargs = {'bImage':bImage}
    ret = GetFile(sURL, open(sFileName, 'wb'),**kwargs)
    if ret==None:
        raise NameError, "Invalid File"
    else:
        return sFileName, sLocalURL




def sWikiToEnglish(sStr):
    '''Takes things like NateDog_%28He is the best%29 and returns NateDog (He is the best).'''
    assert 0, 'Use urllibs unquote!'
    li = sorted(liFindAll(sStr, '%'))
    for iIndex in range(len(li)-1):
        if li[iIndex] + 1 == li[iIndex+1]:
            li[iIndex] = li[iIndex+1] = -1
    li = [i for i in li if i != -1]
    ls = [sStr[i+1:i+3] for i in li]
    sRet = sStr
    for s in ls:
        sRet = sRet.replace('%%%s' % (s), chr(int(s, 16)))
    sRet = sRet.replace('%%', '%').replace('_', ' ')
    return sRet

def sEnglishToWiki(sStr):
    '''Does the opposite of sWikiToEnglish'''
    assert 0, 'use urllibs quote!'
    sStr = sStr.replace('%', '%%')
    sStr = sStr.replace('--', '%E2%80%93')
    lsBads = ["'", '(', ')', '<', '>']
    lsGoods = ['%' + hex(ord(s))[2:] for s in lsBads]
    for sBad, sGood in zip(lsBads, lsGoods):
        sStr = sStr.replace(sBad, sGood)
    sStr = sStr.replace(' ', '_')
    return sStr

def sWikiURLFromEntry(sEntity):
    #sRet = 'http://en.wikipedia.org/wiki/%s' % (sEnglishToWiki(sEntity))
    sEntity = '+'.join(quote(sEntity).split())
    sRet = 'http://en.wikipedia.org/wiki/Special:Search?search=%s&go=Go' % (sEntity)
    return sRet

def sWikiSearchURLFromEntry(sEntity):
    sEntity = '+'.join(quote(sEntity).split())
    sRet = 'http://en.wikipedia.org/wiki/Special:Search?search=%s&fulltext=Search&limit=1000' % (sEntity)
    return sRet

def sYouTubeSearchURL(sStr):
    sStr = '+'.join(quote(sStr).split())
    sRet = 'http://www.youtube.com/results?search_query=%s&search=Search' % (sStr)
    return sRet

def lxIntersperseList(lxOriginal, lxIntersperser):
    '''Returns a new list, composed of the elements of lxOriginalList, with the next item of lxIntersperser between each.
    lxIntersperseList([1, 3, 5, 7], [2, 4, 6, 8]) => [1, 2, 3, 4, 5, 6, 7]'''
    lxRet = []
    if len(lxOriginal) < 2:
        lxRet = copy.copy(lxOriginal)
    else:
        for i in range(len(lxOriginal)-1):
            lxRet.append(lxOriginal[i])
            lxRet.append(lxIntersperser[i])
        lxRet.append(lxOriginal[i+1])
    return lxRet

def lsSplitAndKeepSpaces(sStr):
    '''lsSplitAndKeepSpaces('Hey, my name is Nate.  Isn't that great?') => ['Hey, ', 'my ', 'name ', 'is ', 'Nate.  ', 'Isn't ', 'that ', 'great?']'''
    sStr = sStr.lstrip()
    lsRet = []
    iStart = 0
    bInSpace = False
    for i in range(len(sStr)):
        if not sStr[i].isspace():
            if bInSpace: #we now have a real char but were in spaces.  so new word!
                lsRet.append(sStr[iStart:i])
                iStart = i
                bInSpace = False
        else:
            bInSpace = True
    lsRet.append(sStr[iStart:])
    return lsRet

def VistaDelete(sFilename):
    '''Vista doesn't like os.remove, so use this instead.'''
    return CommandLineCalls(['del "%s"' % sFilename])

def StartFile(sFilename):
  '''Like os.startfile() but works on XP and debian systems.
    This doesn't actually work, I don't know why.'''
  if sys.platform == 'win32':
    return os.startfile(sFilename)
  elif sys.platform == 'linux2':
    return os.spawnl(os.P_WAIT, 'run-mailcap %s' % sFilename)
  else:
    assert 0, 'FIND A WAY TO LAUNCH ARBITRARY FILES ON YOUR OS!'

#def KillProcess(sProc):
#    '''This is taken from Marc Hammond.'''
#    import win32api, win32pdhutil, win32con
#    if sys.platform != 'win32':
#        assert 0, 'Figure this out for linux!'
#    try:
#        win32pdhutil.GetPerformanceAttributes('Process','ID Process',sProc)
#    except:
#        pass
#
#    liPids = win32pdhutil.FindPerformanceAttributesByName(sProc)
#
#    assert len(liPids) == 1, 'I\'m confused about which one to kill!'
#    hProc = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, liPids[0])
#    win32api.TerminateProcess(hProc,0)
#    win32api.CloseHandle(hProc)
#    result = ""

    
def sRemoteCall(sMachine, sFunction, bEscape, **kwargs):
    '''To call PresentShow, for example you might do:
    sRemoteCall(NEWS_AT_SEVEN_SERVER_URL, 'PresentShow', False, sShowXML=sXML)
    You're probably better off using the newer RemoteMachine below.'''
    if bEscape:
        for k in kwargs:
            kwargs[k] = escape(kwargs[k])
    params = urllib.urlencode(kwargs)
    sURL = sMachine + sFunction
    
    try:
        sRet = urllib.urlopen(sURL, params).read()
    except TypeError:
        assert 0, 'I don\'t think there is a function named %s running on %s!  Are you sure that function is exposed and attached to the root?' % (sFunction, sMachine)
    return unescape(sRet)

#print sRemoteCall('http://animatron4000.cs.northwestern.edu:2718/', 'find_entities', False, text='George W. Bush')

class RemoteMachine:
    '''A nice little abstraction of a remote machine that has some webservices running on it.
    You can do things like 
    foo = RemoteMachine(url, 80)
    foo.do_remote_function()
    and it will work.  There are also some shortcuts on what you can pass in as the url, if it is 
    a machine here on the cs.northwestern.edu domainsubnet thing, just use the normal name.
    So you can do  
    bar = RemoteMachine('jermaine')
    for http://jermaine.cs.northwestern.edu:80/'''
    def __init__(self, url, port=80):
        if url[-1] == '/':
            url = url[:-1]
        if url == 'localhost':
            url = 'http://localhost:%s/' % (port,)
        elif '.' not in url:
            url = 'http://%s.cs.northwestern.edu' % (url)
            url = '%s:%s/' % (url, port)
        else:
            url = '%s:%s/' % (url, port)
        self.url = url
    def __handle_call__(self, func_name, *args, **kwargs):
        if args and not kwargs:
            raise TypeError, "You have %s arguments that aren't keyword arguments!  You can't do this over the network!  You can't do foo(bar, baz), you have to do foo(bar=baz, nar=narbar)!" % (len(args))
        params = urllib.urlencode(kwargs)
        url = self.url + func_name
        try:
            #print "URL OPENING"
            #print url
            #print params
            ret = urllib.urlopen(url, params).read()
            #print ret
        except IOError:
            raise IOError, "I don't think a machine is up and running at %s" % (self.url)
        except Exception:
            raise Exception, "COULDN'T HANDLE URL: %s" % (url)
        if '404 Not Found' in ret:
            raise AttributeError, "I don't think %s is a real function on %s.  Did you forget to cherrypy.expose it or anythign?" % (func_name, self.url)
        return ret
    def __getattr__(self, func_name):
        ret = (lambda *args, **kwargs: self.__handle_call__(func_name, *args, **kwargs))
        return ret

#anim = RemoteMachine('animatron4000', 2718)
#print anim.find_entities(text='George W. Bush')

def sUnescape(s):
    assert 0, 'Use sXMLUnescape'
    s = unescape(s, {'&quot;': '"'})
    s = s.replace('&#39;', "'")
    return s

def lxReversedItems(lx):
    '''lxReversedItems([[1, 2], [3, 4], [5, 6]]) => [[2, 1], [4, 3], [6, 5]]
    foo is not lxReversedItems(foo)'''
    lxRet = []
    for x in lx:
        xNew = []
        for p in reversed(x):
            xNew.append(p)
        lxRet.append(xNew)
    return lxRet

def lsGetAllFilesFromDirectory(sDir):
    '''Recurses and returns a list of absolute paths.'''
    lsRet = []
    for s in os.listdir(sDir):
        sFullPath = sPathJoin(sDir, s)
        if os.path.isdir(sFullPath):
            lsRet += lsGetAllFilesFromDirectory(sFullPath)
        else:
            lsRet.append(sFullPath)
    return lsRet

def dFindRuns(lsWords, llsAnims):
    '''I don't think this is actually used anywhere.

    dFindRuns('my name is nate'.split(), [['A1'], ['A1', 'A2'], ['A1', 'A2', 'A3'], ['A4']]) ==> {'A1': ['my name is'], 'A3': ['is'], 'A2': ['name is'], 'A4': ['nate']}'''
    assert len(lsWords) == len(llsAnims), '%s %s' % (lsWords, llsAnims)
    dRet = {}
    for i, ls in enumerate(llsAnims):
        for s in ls:
            j = i
            while j < len(llsAnims) and s in llsAnims[j]:
                j += 1
            if s not in dRet:
                dRet[s] = []
            dRet[s].append(' '.join(lsWords[i:j]))
            for k in range(i, j):
                del llsAnims[k][llsAnims[k].index(s)]
    return dRet

def lReplace(lx, xOld, xNew):
    '''Works like replace on strings but for lists. So,
    lReplace(['hey', 'my', 'name', 'is', 'nar'], 'name', 'butt') => ['hey', 'my', 'butt', 'is', bar']'''
    lxRet = ['a'] * len(lx)
    for i,x in enumerate(lx):
        if x == xOld:
            lxRet[i] = xNew
        else:
            lxRet[i] = x
    return lxRet

def lbIntToBinary(iInt, iTotalBytesWanted):
    '''Takes an int and how long you want the return array to be, and returns a list of booleans.
    lbIntToBinary(9, 6) = ['False', 'False', 'False', 'True', 'False', 'False', 'True'] '''
    iMax = 0
    while 2 ** iMax <= iInt:
        iMax += 1
    lbRet = []
    for i in range(iMax):
        if 1<<i & iInt:
            lbRet.append(True)
        else:
            lbRet.append(False)
    lbRet.reverse()
    lbRet = [False] * (iTotalBytesWanted - len(lbRet)) + lbRet
    return lbRet

def llxAllPossibleCombinations(lxThings):
    '''This little guy returns all possible combinations of the items in lxThings.  The order is meaningless.
    llxAllPossibleCombinations([1, 2, 3]) => [[1], [2], [3], [1, 2], [2, 3], [1, 3], [1, 2, 3]]
    My implementation, if I do say so myself, is slick.  Albeit incomprehensible.'''
    llxRet = []
    for i in range(2**len(lxThings)):
        innerLst = [x for x, b in zip(lxThings, lbIntToBinary(i, len(lxThings))) if b]
        if len(innerLst) > 0:
            llxRet.append(innerLst)
        #llxRet.append([x for x, b in zip(lxThings, lbIntToBinary(i, len(lxThings))) if b])
    return llxRet



def first(lx, test, *args, **kwargs):
    '''Takes a list, a test, and, possibly, args for the test.  Returns the first element that passes the test.
    (Each element is tried as the first argument to test, with *args and **kwargs being the following arguments.)
    first([1, 3, 5, 42, 15], (lambda x: x % 2 == 0)) => 42'''
    for x in lx:
        if test(x, *args, **kwargs):
            return x
    return None

def benchmark(f):
    '''@condition.
    This will see how long a function takes to run, and if longer than 0, will print the runtime when the function exits.
    so
    @benchmark
    def SlowFunction():
        print 'Blah pretend I'm slow.'
    SlowFunction()
    
    will do something like
    'Function SlowFunction took 3.211274' '''
    def foo(*args, **kwargs):
        fStartTime = time.time()
        ret = f(*args, **kwargs)
        fTotal = time.time() - fStartTime
        if fTotal > 0.0:
            print 'Function %s took %s' % (f.func_name, fTotal)
        return ret
    return foo

def stopwatch(f, *args, **kwargs):
    '''About the same thing as the @benchmark condition above, but you use it
    when calling the slow function, not defining the slow function.  So you could do
    
    stopwatch(SlowFunction, SlowFunctionArg1)
    
    and get
    'Function SlowFunction took 3.211274' '''
    fStartTime = time.time()
    ret = f(*args, **kwargs)
    fTotal = time.time() - fStartTime
    if fTotal> 0.0:
        print 'Function %s took %s' % (f.func_name, fTotal)
    return ret

class FileAndConsolePrinter:
    def __init__(self, sFilename):
        import sys
        self.__hConsole = sys.stdout
        self.__hFile = open(sFilename, 'w')
    def write(self, s):
        self.__hConsole.write(s)
        self.__hFile.write(s)
    def close(self):
        self.__hFile.close()

def DumpToDebug(f, *args, **kwargs):
    '''This nice guy will call f(*args, **kwargs) with the standard print statement
    mapped to write to DEBUG_OUTPUT.'''
    return DumpToFile(DEBUG_OUTPUT, f, *args, **kwargs)
def DumpToFile(sFilename, f, *args, **kwargs):
    '''This is the same as DumpToDebug, but you specify the filename of the dump
    as DumpToFiles first argument.  Note that you specify the name of a file,
    NOT a handle to it.'''
    fOut = FileAndConsolePrinter(sFilename)
    import sys
    old = sys.stdout
    sys.stdout = fOut
    ret = f(*args, **kwargs)
    sys.stdout = old
    fOut.close()
    return ret

def llSplitNWays(l, n, bShuffle=True):
    '''This little bit of sweetness takes a list, l, and an int, n.
    It will return a list of n lists that, combined, compose l.
    bShuffle works as expected.
    For example,
    llSplitNWays([1, 2, 3, 4, 5, 6], 3) might yield
    [[1, 4], [2, 3], [6, 5]].'''
    iTotal = len(l)
    if bShuffle:
        random.shuffle(l)
    iStep = int(iTotal / n)
    llRet = []
    for i in range(n):
        llRet.append(l[i * iStep: i * iStep + iStep])
    for i in range(n * iStep, len(l)):
        llRet[i % len(llRet)].append(l[i])
    return llRet

def fAmountOutOfRange(lfQuery, llfRanges):
    '''Takes a list a list of ranges like
    [[1.0, 2.1], [4.2, 68]]
    and a query like
    [4.1, 5.6]
    and will return the amount of range in the query that isn't contained in the ranges
    of llfRanges.  So, for the above examples, would return .1
    (HINT: This is useful for event start and end timings.)'''
    assert len(lfQuery) == 2, 'Lfquery is %s' % lfQuery
    if lfQuery[1] <= lfQuery[0]:
        return 0.0
    llfStarts = [l for l in llfRanges if l[0] <= lfQuery[0] and l[1] > lfQuery[0]]
    if llfStarts:
        fRet = fAmountOutOfRange([max(l[1] for l in llfStarts), lfQuery[1]], llfRanges)
        assert fRet >= 0.0, '%s %s' % (lfQuery, llfRanges)
        return fRet
    else:
        try:
            fNext = min(l[0] for l in llfRanges if l[0] >= lfQuery[0] and l[0] < lfQuery[1])
        except ValueError:
            return lfQuery[1] - lfQuery[0]
        fRet = fNext - lfQuery[0] + fAmountOutOfRange([fNext, lfQuery[1]], llfRanges)
        assert fRet >= 0.0, '%s %s' % (lfQuery, llfRanges)
        return fRet

def bIsTitle(sString):
    '''A more forgiving version of the string classes istitle().  Makes sure all words but stopwords have their first letter capitalized.
    The stopword list is local to the function.'''
    lsStopWords = 'a and about an are as at be by for from in is it of on or that the this to was will with the ph dr. jr.'.split()
    for s in sString.split():
        if s.isalpha() and s.lower() not in lsStopWords and s[0].islower() and '-' not in s:
            return False
    return True

def sKillParentheses(sStr):
    '''Takes a string, returns a string with all parenthesized phrases removed.
    Doesn't work for nested parentheses.
    'far far (42) far' => 'far far  far' '''
    return sKillTags(sStr, '(', ')')

def sKillNonQuotedParentheses(sStr):
    '''Like sKillParentheses above, but won't kill parentheses inside quotes.
    sKillNonQuotedParentheses('Robert Redford (noted actor) said "(I think I am) really cool"') ->
    Robert Redford  said "(I think I am) really cool".
    This function will munge spaces and stuff, and only works on double-quotes.'''
    ret = sStr
    liQuoteIndices = liFindAll(sStr, '"')
    if len(liQuoteIndices) % 2 == 0: # make sure we're confident we have matched quotes
        for i in range(1, len(liQuoteIndices), 2):
            liQuoteIndices[i] += 1
        lsParts = lsSplitAtIndices(sStr, liQuoteIndices)
        #now even parts are unqouted, odd parts are quoted
        for i in range(0, len(lsParts), 2): #skip quoted parts
            lsParts[i] = sKillParentheses(lsParts[i])
        ret = ' '.join(lsParts)
    return ret
    
    

def __kill_tags(text, start, finish):
    import inspect
    assert len(start) == len(finish) == 1, 'tags can only be one character!'
    while True:
        start_index = text.find(start)
        finish_index = text.find(finish, start_index)
        if start_index == finish_index or start_index < 0 or finish_index < 0:
            break
        else:
            text = text[:start_index] + text[finish_index+len(finish):]
    return text


def sKillTags(text, *args):
    '''Takes a string, and a list of args, assumed to be in (start, close, start, close...) format.
    and returns a new string that is the same as the previous
    except for everything between the start and finish tags has been removed.
    Each tag can only be one letter long.
    sKillTags('Nate "Badass" Nichols is great', '"', '"') -> 'Nate Nichols is great' '''
    assert len(args) % 2 == 0, "Need an even number of args!"
    for i in range(0, len(args), 2):
        text = __kill_tags(text, args[i], args[i+1])
    return text 
    
def lsFindTagged(sStr, sStartTag, sStopTag):
    '''Returns all the strings that were found between sStartTag and sStopTag in sStr.
    So lsFindTagged('Nate is the <b>best!</b>', '<b>', '</b>') => ['best!']'''
    lsRet = []
    iStart = 0
    while sStr.find(sStartTag, iStart) != -1:
        iStart, iEnd = sStr.find(sStartTag, iStart), sStr.find(sStopTag, iStart)
        #print iStart, iEnd
        while sStr[iStart] != '>':
            iStart += 1
            if iStart == len(sStr):
                break
        #print iStart, iEnd
        if iEnd != -1:
            lsRet.append(sStr[iStart+1:iEnd])
        iStart = iEnd + 1 #don't want to find the same thing again
    return lsRet

def lsCapitalizedPhrases(text):
    '''Returns a list of phrases that are capitalized.
    lsCapitalizedPhrases('I saw Bill Clinton talking to Duane "Dog" Chapman') -> ['I', 'Bill Clinton', 'Duane "Dog" Chapman']'''
    ret = []
    in_phrase = False
    for word in text.split():
        if word[0].isupper() or (sStripNonAlNum(word) and sStripNonAlNum(word)[0].isupper()) or word.startswith('al-'):
            if in_phrase:
                ret[-1] += ' ' + word
            else:
                ret.append(word)
                in_phrase = True
        else:
            in_phrase = False
        if word[-1] in ('?', '!'):
            in_phrase = False
        if word[-1] == '.' and len(word) > 2 and word[-2].islower():
            in_phrase = False
    return ret 
    
def sStripNonAlNum(sStr,lsExceptions=[]):
    '''Strips leading and trailing non alnum characters and returns a new string.
    sStripNonAlNum('# !!*FooBar---') => 'FooBar' '''
    i = 0
    while i < len(sStr) and not sStr[i] in lsExceptions and not sStr[i].isalnum():
        i += 1
    j = len(sStr) - 1
    while j > i and not sStr[j] in lsExceptions and not sStr[j].isalnum():
        j -= 1
    return sStr[i:j+1]

def sStripStopWords(sStr, *args, **kwargs):
    '''Strips leading and trailing stop words.  Will munge spaces.'''
    if not sStr:
        return sStr
    lsWords = sStr.split()
    while lsWords and bIsStopWord(lsWords[0], *args, **kwargs):
        lsWords.pop(0)
    while lsWords and bIsStopWord(lsWords[-1], *args, **kwargs):
        lsWords.pop(-1)
    return ' '.join(lsWords)
        

def sScrubNonAlNum(sStr, bGoEasyOnUnicode=False):
    '''String will only have strings, numbers, and spaces.'''
    if bGoEasyOnUnicode:
        sRet = ''.join([cCharMap(ord(c)) for c in list(sStr.strip()) if c.isalnum() or c.isspace() or 127 < ord(c) < 255 or c == ')' or c == '('])
    else:
        sRet = ''.join([cCharMap(ord(c)) for c in list(sStr.strip()) if c.isalnum() or c.isspace()])
    return sRet

def lsPullQuotes(sStr):
    '''Takes a string, returns a list of all the quoted things in the string, with opening quotes still attached.'''
    lxQuotes = []
    lsRet = []
    for i in range(len(sStr)):
        if sStr[i] == '"' or sStr[i] == "'":
            if i > 0 and i < len(sStr) - 1 and sStr[i] == "'" and sStr[i-1].isalpha() and sStr[i+1].isalpha():  #so we won't split on quotes in contractions
                continue
            if lxQuotes and lxQuotes[-1][0] == sStr[i]: #we're matching a pair
                lsRet.append(sStr[lxQuotes[-1][1]:i])
                lxQuotes.pop()
            else:
                lxQuotes.append([sStr[i], i])
    return lsRet

def CommandLineCalls(lsCalls, sDir='', bQuiet=False):
    '''Writes all the things in lsCalls to a temporary file, then calls that as a batch process.
    Windows CLI is sketchy and I don't grok it's slash conventions, etc.  This side steps a lot of that.
    If bQuiet, all output is suppressed.'''
    if bQuiet:
        print 'WARNING, if this call dies, leave bQuiet off.  I have no idea why.'
    sTempFilename = sPathJoin(DEBUG_DIR, 'OK_TO_DELETE.bat')
    out = open(sTempFilename, 'w')
    for s in lsCalls:
        out.write(s.replace(r'%', r'%%')) #i think % is the batch file comment char
    out.close()
    sOldDir = os.getcwd()
    if sDir:
        os.chdir(sDir)
    if bQuiet:
        os.popen4(sTempFilename)
    else:
        os.system(sTempFilename)
    try:
        os.remove(sTempFilename)
    except OSError, e:
        print 'Was unable to delete the temp filename, err was %s', e 
        
    os.chdir(sOldDir)

def lsCommandLineCall(sCall, sDir=''):
    '''Kind of like CommandLineCalls above, but doesn't write to a batch file.
    So, you're in charge of watching your slashes and all.  But, this will return alloutput
    from sCalls.  Kind of coming at it from a different angle.'''
    
    lsRet = os.popen4(sCall)[1].readlines()


    return lsRet

def lxSplit(sStr, sSplit=' '):
    '''Splits sStr on the string sSplit.  It works similarly to str.split(),
    but instead of just returning a list of substrings, it returns a list of
    two-element lists, where the first element is the substring and the second
    element is the int index where that substring is.
    lxSplit('hey look at me') => [['hey', 0], ['look', 4], ['at', 9], ['me', 12]]
    THIS WON"T HANDLE NEWLINES AS YOU WOULD PROBABLY EXPECT IT TO.'''
    iStart = -1
    lxRet = []
    for i in range(len(sStr)):
        if sStr[i] == ' ':
            if iStart != i - 1:
                lxRet.append([sStr[iStart+1:i], iStart+1])
            iStart = i
    lxRet.append([sStr[iStart+1:i+1], iStart+1])
    return lxRet

def sFixDownloadURL(sURL):
    '''"Fixes" the download urls. (unescapes the url escape chars.)  I don't know why the replace() call is necessary,
    but google video has double amp; s in its links.  Weird.'''
    sRet = unescape(sURL).replace('amp;', '')
    if __bDebug:
        print 'Converted %s to %s for link' % (sURL, sRet)
    return sRet

#def sFixPronunciations(sStr):
#    '''Does a flatfooted replacement of the customized pronunciations in dPronunciations here.'''
#    assert 0, 'Use the real neospeech voice replacement stuff.'
#    for k in dPronunciations:
#        sStr = sStr.replace(k, dPronunciations[k])
#    return sStr

def sKillUnicodeEscapes(sStr):
    '''This is a weird thing and its existence strongly implies that I'm missing something obvious.
    I think that Googlevideo or Youtube (i don't remmeber which) escapes HTML/XML unfriendly characters by
    writing them as unicode escapecharacters (ie '\u00ab')
    So, this function finds those and replaces them with their normal character.'''
    sRet = ''
    i = 0
    while i < len(sStr):
        if sStr[i] == '\\' and sStr[i+1] == 'u' and sStr[i-1] != '\\':
            if __bDebug:
                print '!',
            sRet += chr(int(sStr[i+2:i+6], 16))
            i += 5
        elif sStr[i] != '\\':
            if __bDebug:
                print '#',
            sRet += sStr[i]
        i += 1
        if __bDebug:
            print len(sRet),
    return sRet

def sHitISA(sRequest):
    '''This is a thing you can use to hit an ISA server, but it's deprecated now.
    The address of the server you hit is above somewhere. in ISA_SERVER and ISA_PORT.'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ISA_SERVER, ISA_PORT))
    except socket.error:
        raise 'I don\'t think ISA is running on %s, %s!' % (ISA_SERVER, ISA_PORT)
    sock.send(sRequest)
    sResponse = sock.recv(10000000)
    sock.close()
    return sResponse

cTooMuchWhitespaceRegex = re.compile('\s\s\s+')

def sKillNewlines(sText):
    '''Takes the extra spaces and newlines and crap that comes out of html sometimes and kills it.'''
    sRet = cTooMuchWhitespaceRegex.sub(' ', sText)
    return sRet

#sLongHyphen = unicode(unichr(226) + unichr(128) + unichr(147))
#sEWithAccentAgue = unichr(233)
#sAWithAccentAgue = unicode(unichr(195) + unichr(161))
#sEWithAccentAgue2 = unicode(unichr(195) + unichr(169))
#sShittyQuote = unicode(unichr(226) + unichr(128) + unichr(153))
#sDumbO = unicode(unichr(0xD0) + unichr(0xBE))
#sAWithAccenAgue = unicode(unichr(195) + unichr(161))

    
#def SafeStr(sText):
#    '''Takes a string, and returns as much as it can of the string that is not unicode.'''
#    try:
#        sText = unicode(sText, 'Latin-1')
#        return sText
#    except TypeError:
#        pass #Unicode represents the worst in everything
#
#    sText = sText.replace(sLongHyphen, '--')
#    sText = sText.replace(sEWithAccentAgue, 'e')
#    sText = sText.replace(sAWithAccentAgue, 'a')
#    sText = sText.replace(sEWithAccentAgue2, 'e')
#    sText = sText.replace(sShittyQuote, "'")
#    sText = sText.replace(sDumbO, 'o')
#    sText = sText.replace(sAWithAccentAgue, 'a')
#
#    ls = list(sText)
#    for i in range(len(sText)):
#        print ls[i], ord(ls[i])
#        if ord(ls[i]) == 146:
#            ls[i] = "'"
#        elif ord(ls[i]) == 147:
#            ls[i] = '"'
#        elif ord(ls[i]) == 148:
#            ls[i] = '"'
#        elif ord(ls[i]) in (131, 132, 133, 134, 160):
#            ls[i] = 'a'
#        elif ord(ls[i]) == 135:
#            ls[i] = 'c'
#        elif ord(ls[i]) == 128:
#            ls[i] = 'C'
#        elif ord(ls[i]) in (130, 136, 137, 138):
#            ls[i] = 'e'
#        elif ord(ls[i]) in (139, 140, 141, 161):
#            ls[i] = 'i'
#        elif ord(ls[i]) in (147, 148, 149, 162):
#            ls[i] = 'o'
#        elif ord(ls[i]) in (129, 150, 151, 163):
#            ls[i] = 'u'
#        elif ord(ls[i]) == 164:
#            ls[i] = 'n'
#        elif ord(ls[i]) > 127:
#            ls[i] = ''
#    sRet = ''.join([c for c in ls if c])
#    return sRet

def SafeStr(text):
    if type(text) is not unicode:
        try:
            text = unicode(text, "utf-8", 'ignore')
        except TypeError, e:
            pass
        #print text
        text = unicodedata.normalize('NFKD', text)
    ret = []
    for c in text:
        if ord(c) in (0x201C, 0x201D):
            ret.append('"')
        elif ord(c) in (0xAD, 0x2013, 0x2014, 0x2015, 0x2212):
            ret.append('-')
        elif ord(c) in (0xB4, 0x2BB, 0x2018, 0x2019):
            ret.append("'")
        elif ord(c) == 0x2026:
            ret.append('...')
        elif ord(c) == 0xAB:
            ret.append('<<')
        elif ord(c) == 0xBB:
            ret.append('>>')
        elif ord(c) == 0x201A:
            ret.append(',')
        elif ord(c) == 0x1C3:
            ret.append('!')
        elif ord(c) in (0xC0, 0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0x100):
            ret.append('A')
        elif ord(c) == 0xC6:
            ret.append('Ae')
        elif ord(c) in (0xC7, 0x10C):
            ret.append('C')
        elif ord(c) in (0xC8, 0xC9, 0xCA, 0xCB):
            ret.append('E')
        elif ord(c) in (0xCC, 0xCD, 0xCE, 0xCF, 0x12A):
            ret.append('I')
        elif ord(c) == 0xD0:
            ret.append('D')
        elif ord(c) == 0xD1:
            ret.append('N')
        elif ord(c) in (0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD8, 0x14C):
            ret.append('O')
        elif ord(c) == 0xD7:
            ret.append('x')
        elif ord(c) in (0xD9, 0xDA, 0xDB, 0xDC):
            ret.append('U')
        elif ord(c) == 0xDD:
            ret.append('Y')
        elif ord(c) in (0xDF, 0x160):
            ret.append('S')
        elif ord(c) in (0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0x101, 0x103, 0x105):
            ret.append('a')
        elif ord(c) == 0xE6:
            ret.append('ae')
        elif ord(c) == 0xE7:
            ret.append('c')
        elif ord(c) in (0xE8, 0xE9, 0xEA, 0xEB, 0x117, 0x119, 0x11B, 0x1EBF):
            ret.append('e')
        elif ord(c) in (0xEC, 0xED, 0xEE, 0xEF, 0x12B, 0x131):
            ret.append('i')
        elif ord(c) in (0xF0, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF8, 0x14D, 0x151, 0x1ECD):
            ret.append('o')
        elif ord(c) == 0xF1:
            ret.append('n')
        elif ord(c) == 0xF7:
            ret.append('/')
        elif ord(c) in (0xF9, 0xFA, 0xFB, 0xFC, 0x16B, 0x16F):
            ret.append('u')
        elif ord(c) in (0xFD, 0xFF):
            ret.append('y')
        elif ord(c) == 0x153:
            ret.append('oe')
        elif ord(c) == 0x144:
            ret.append('n')
        elif ord(c) == 0x130:
            ret.append('I')
        elif ord(c) in (0x107, 0x10D, 0x163):
            ret.append('c')
        elif ord(c) in (0x15B, 0x15F, 0x161):
            ret.append('s')
        elif ord(c) == (0x15A, 0x160):
            ret.append('S')
        elif ord(c) == 0x142:
            ret.append('l')
        elif ord(c) == 0x11F:
            ret.append('g')
        elif ord(c) in (0x14F, 0x1E6D):
            ret.append('t')
        elif ord(c) in (0x17A, 0x17E):
            ret.append('z')
        elif ord(c) in (0x17B, 0x17D):
            ret.append('Z')
        elif ord(c) == 0x39C:
            ret.append('M')
        elif ord(c) == 0x159:
            ret.append('r')
        elif ord(c) > 128:
            pass
          #  print c, ord(c), text, ', '.join([str(ord(c)) for c in text])
        else:
            ret.append(c)

    ret = ''.join(ret)
    ret = ret.encode('ASCII', 'ignore')
    return ret

def lsIntersection(lsLHS, lsRHS, bIgnoreCase=True):
    '''An easy set intersection that returns a list of all the elements that are
    in lsLHS and lsRHS.  It assumes they're lists of strings, and strips them
    before comparing.  If you'd like, it will also ignore case.'''
    if bIgnoreCase:
        lsLHS = [s.lower() for s in lsLHS]
        lsRHS = [s.lower() for s in lsRHS]
    lsLHS = [s.strip() for s in lsLHS]
    lsRHS = [s.strip() for s in lsRHS]
    lsRet = []
    for s in lsLHS:
        if s in lsRHS:
            lsRet.append(s)
    return lsRet

def lsSplitAtIndices(sText, liSplitIndices):
    '''Takes a string, sText, and returns a list of strings made by splitting sText at the indices in liSplitIndices.
    so lsSplitAtIndices('Foobarbaz', [1, 4, 6]) => ['F', 'oob', 'ar', 'baz'] (I think).  That's defintiely the idea, but my counting may be off.  FENCEPOST!'''
    if not liSplitIndices:
        return [sText]
    ins = sorted(liSplitIndices)    
    if ins[0] != 0:
        ins = [0] + ins
    lsRet = []
    for i in range(len(ins) - 1):
        if ins[i+1] - ins[i] <= 1:
            continue
        lsRet.append(sText[ins[i]:ins[i+1]])
    lsRet.append(sText[ins[-1]:])
    return lsRet

def lsSplitMany(sText, lsSplitters):
    '''Like str.split() but takes a list of splitters to split over.'''
    lsRet = [sText]
    for sSplitter in lsSplitters:
        lsRet = reduce(lambda x, y: x + y, [s.split(sSplitter) for s in lsRet])
    return lsRet

def tFindAny(sText, lsSubs, *args, **kwargs):
    '''Takes a big string and a list of possible substrings.  Returns the 
    a tuple, first element is found substring, second is index.  Returns the first
    one it finds.  If nothing found, returns ('', -1), args and kwargs get passed to
    str.find()'''
    ret = ('', -1)
    dMatches = {}
    for sSub in lsSubs:
        i = sText.find(sSub, *args, **kwargs)
        if i != -1:
            dMatches[sSub] = i
    if dMatches:
        iLowest = min(dMatches.values())
        for sKey in dMatches:
            if dMatches[sKey] == iLowest:
                ret = (sKey, iLowest)
                break
    return ret

def liFindAll(sText, sSub, liIgnore=[], bIgnoreCase=True, bFindEnd=False):
    '''Takes a string sText and a substring sSub.  Returns a list of all the
    indices where sSub occurs in sText.  (It repeatedly calls .find and
    collects the results.)
    The search will ignore any indices in liIgnore.
    bIgnoreCase does what you'd expect it to.
    bFindEnd returns the index at the end of the word, instead of the start.'''
    ret = []
    nextIndex = -1
    if bIgnoreCase:
        sText, sSub = sText.lower(), sSub.lower()
    while True:
        nextIndex = sText.find(sSub, nextIndex + 1)
        if nextIndex == -1:
            return ret
        else:
            if nextIndex not in liIgnore:
                if bFindEnd:
                    nextIndex += len(sSub)
                ret.append(nextIndex)

def liFindAnyOverAll(sText, lsSubs, *args, **kwargs):
    '''Just like liFindAll, but takes a list of strings to search for instead of a single one.
    If you search for one string that is a substring of another, expect to not get the results you want.
    ie, don't search for 'fork' and 'forkenheim' '''
    ret = []
    for sSub in lsSubs:
        ret += liFindAll(sText, sSub, *args, **kwargs)
    return ret

def sScrubMarkup(text):
    for regex in _markup_regexes:
        text = regex.sub('', text)
    text = _space_regex.sub('  ', text)
    return text


def sScrubMarkupComments(s):
    '''Takes something like '<HTML>Foo <!--this is a comment--> bar</HTML>' and returns '<HTML>Foo  bar</HTML>'''
    s = _markup_regexes[0].sub('', s)
    return s

def removeHTML(sText):
    lsText = lsSplitOnMarkup(sText,lsIgnore=[])
    return ' '.join([text for text in lsText]).strip()

def lsSplitOnMarkup(sText, lsIgnore=['p', 'a', 'br', 'img', 'strike', 'em', 'ul', 'li'], bTryBest=True):
    '''Takes a string with html in it, and returns a list of strings that are split on the markup.  Ignores tags in lsIgnore.
    If bTryBest, will try to pull out stupid entries.'''
    sText = sText.replace('&nbsp', '')
    sText = sText.replace('&lt', '<')
    sText = sText.replace('&rt', '>')
    depth = 0
    i = -1
    lsTricky = ['script', 'SCRIPT', 'style', 'STYLE']
    lsRet = ['']
    bCollectingTag = False
    while i < len(sText)-1:
        i += 1
        letter = sText[i]
        if letter == '<':
            bCollectingTag = True
            depth += 1
            tagCollect = ''
            if __bDebug:
                print 'Moving IN at %s, %s' % (i, sText[i:i+10])
                print 'DEPTH: %s' % (depth)
        elif letter == '>':
            if tagCollect not in lsIgnore and tagCollect[1:] not in lsIgnore:
                #this is a big tag change so we need to start a new block
                lsRet.append('')
            lsRet[-1] += ' '
            depth -= 1
            depth = max(depth, 0)
            if __bDebug:
                print 'Moving OUT at %s, %s' % (i, sText[i:i+10])
                print 'DEPTH: %s' % (depth)
        elif depth == 0:
            lsRet[-1] += letter
        else: #in markup tag
            if letter == ' ':
                bCollectingTag = False
            if bCollectingTag:
                tagCollect += letter            
            #lsTricky is a little tricky because it doesn't need to mind it's brackets.  So we skip it.  This may be a problem if someone in the script has a string '/script' or something
            if tagCollect in lsTricky:
                iEndOfScript = sText.find('/' + tagCollect, i)
                i = iEndOfScript + len(tagCollect) + 1 #+1 to get past /
                depth -= 1
    lsRet = [s.strip() for s in lsRet if s.strip()]
    if bTryBest:
        fMax = float(max([len(s) for s in lsRet]))
        lsRet = [s for s in lsRet if len(s) / fMax > .1]
    return lsRet

def dFlipDict(d):
    '''dFlipDict({k1:v1, k2:v1, k3:v2}) => {v1:[k1, k2], v2:[k3]}'''
    ret = {}
    for k, v in d.iteritems():
        if v not in ret:
            ret[v] = []
        ret[v].append(k)
    return ret

def iSizeOfRemote(sURL):
    '''Takes a url and returns the size of the file at the URL.  It follows redirects,
    too, I think.  (It uses urllib.urlopen, so it does whatever that does.)
    This DOESN'T CATCH ANY EXCEPTIONS!'''
    try:
        f = urllib.urlopen(sURL)
    except IOError:
        return -1
    #print int(f.info().get('content-length', -1))
    return int(f.info().get('content-length', -1))

def iSizeOfLocal(sFilename):
    '''Like iSizeOfRemote, but for local file.  Some enterprising individual
    should write a function that uses lexographic ("50 cents, please!") information
    about the string getting passed into to call the appropriate iSizeOf*,
    but that individual is not me!'''
    return os.stat(sFilename)[6]

def __getFile(open_func, sURL, hOutputFile=None, bVerbose=False,bImage=False):
    '''Pulls the file from sURL.  if hOutputFile, it will write the data to it,
    else it returns the data.  It tries to be clever about not hitting the same
    site too frequently (so that they don't figure out we're robots.)  So,
    you shouldn't need to do your own slow-downs; if a site complains, change
    TIME_BETWEEN_HITS above.  This also uses the useragent done at the start of
    this module.'''
    #print "__getFile bImage %s" % bImage
    
    if bVerbose:
        print 'Getting', sURL, 
    ret = ''
    if not sURL.startswith('http://'):  #just a local file
        return open(sURL).read()
    i = sURL.find('/', 8)
    sPrefix = sURL[:i]
    iTimeBetweenHits = sPrefix in TIME_BETWEEN_HITS and TIME_BETWEEN_HITS[sPrefix] or TIME_BETWEEN_HITS['default']
    LastHitLock.acquire()
    
    if sPrefix in LAST_HITS and time.time() - LAST_HITS[sPrefix] < iTimeBetweenHits:
        f = iTimeBetweenHits - (time.time() - LAST_HITS[sPrefix])
        f = max(0, f)
        time.sleep(f)
    
    LAST_HITS[sPrefix] = time.time()
    LastHitLock.release()
    fStartTime = time.time()
    iTriesSoFar = 0
    while iTriesSoFar < 2:
        try:
            webPage = open_func(sURL)
        except (IOError, socket.error):
            raise IOError, "Yeah this page is broken"
            #print 'WEIRD!  SOCKET TIMED OUT TRYING TO OPEN %s!!  I\'M SLEEPING FIVE SECONDS THEN TRYING AGAIN!' % (sURL)
            #time.sleep(5)
        except:
            raise
        else:
            break        
        iTriesSoFar += 1
    try:
        iTotalBytes = iSizeOfRemote(sURL)
    except IOError:
        iTotalBytes = -1
    iBytesSoFar = 0
    iPrintCount = 0
    iTriesSoFar = 0
    while True:
        try:
            data = webPage.read(8192)
        except (IOError, socket.error,UnboundLocalError):
            print 'WEIRD!  SOCKET TIMED OUT TRYING TO OPEN %s!!  I\'M SLEEPING FIVE SECONDS THEN TRYING AGAIN!' % (sURL)
            time.sleep(5)
            iTriesSoFar += 1
            if iTriesSoFar >= 2:
                raise IOError, "Yeah this thing doesn't work"
            continue
        iBytesSoFar += 8192
        iPrintCount += 1
        if bVerbose and iPrintCount % 5 == 0:
            if iTotalBytes != 0:
                print iTotalBytes
                print '%s%%' % (int(100 * float(iBytesSoFar) / iTotalBytes)),
        if not data:
            break
        if hOutputFile:
            hOutputFile.write(data)
        else:
            ret += data
    webPage.close()
    fEndTime = time.time()
    if bVerbose:
        print 'GetFile took ~ %s' % (fEndTime-fStartTime)

    if iBytesSoFar <= 16384 and bImage==True:
        print "NOT ENOUGH BYTES - CORRUPT FILE"
        print iBytesSoFar
        return None
    else:
        return ret



def GetFile(*args, **kwargs):#sURL, hOutputFile=None, bVerbose=False):
    #print "GETFILE " 
    ##print args
    #print "GETFILE" 
    #print kwargs
    myUrlclass = urllib.FancyURLopener()
    return __getFile(myUrlclass.open, *args, **kwargs)

def GetFileWithCookies(*args, **kwargs):
    import urllib2, cookielib
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
    return __getFile(opener.open, *args, **kwargs)

def DownloadFile(sURL, sFilename):
    '''Takes the file at sURL at puts it at sFilename.'''
    outputFile = None
    
    if __bDebug:
        print 'About to download %s to %s' % (sURL, sFilename)
    try:
        outputFile = open(sFilename,"wb")
        print '*******************************'
        print 'opening file here %s %s' % (sURL,sFilename)
    except IOError:
        print 'SOMETHING SCREWED UP TRYING TO OPEN |%s| !!!!!!!!!  IS THERE AN INVALID CHARACTER IN THERE?!  WHY DIDN\'T YOU CATCH IT?!?!??!!?' % sFilename
    try:
            print "OPENING FILE HERE 2 %s %s" % (sURL,sFilename)
            GetFile(sURL, outputFile)
    
    except IOError:
        print "IOERROR"
        outputFile.close()
        return None
    outputFile.close()
    return True

class __DownloadThread(threading.Thread):
    '''Used by DownloadFiles, don't use on your own.'''
    def __init__(self, sURL, sFilename):
        self.sURL, self.sFilename = sURL, sFilename
        threading.Thread.__init__(self)
    def run(self):
        DownloadFile(self.sURL, self.sFilename)

def DownloadFiles(llsNames):
    '''Takes a list of [sURL, sFilename] pairs and downloads them all concurrently.'''
    lThreads = [__DownloadThread(l[0], l[1]) for l in llsNames]
    [t.start() for t in lThreads]
    [t.join() for t in lThreads]

def iSecondsFromString(sStr):
    '''Takes something in the form '3 min 41 sec' and returns 221.
    If it gets confused (not that hard to confuse it), it returns -1.'''
    iRet = 0
    ls = sStr.split()
    try:
        while not ls[0].isdigit(): #gets rid of starting stuff
            ls = ls[1:]
    except IndexError: # this isn't a valid date time thing
        return -1
    for i in range(len(ls)):
        if not ls[i].isdigit():
            continue
        if ls[i+1] == 'min':
            iRet += 60 * int(ls[i])
        else:
            iRet += int(ls[i])
    return iRet  
    
def fPriceFromString(sStr):
    '''Takes something like "$58.99" and returns the float 58.99'''
    return float(sStr.strip().strip('$'))

def bEndsWithIn(sStr, ls, bIgnoreCase=True):
    '''if sStr endswith() anything in ls, true is returned, else false.  bIgnoreCase
    does what you'd expect.'''
    if bIgnoreCase:
        for s in ls:
            if sStr.lower().endswith(s.lower()):
                return True
        return False
    for s in ls:
        if sStr.endswith(s):
            return True
    return False

def AdditiveUpdate(dLHS, dRHS):
    '''Self-documenting, pwn3d!'''
    for k in dRHS:
        if k in dLHS:
            dLHS[k] += dRHS[k]
        else:
            dLHS[k] = dRHS[k]

def NonDestructiveUpdate(dLHS, dRHS):
    '''Two for two in self-documenting update functions!  PWN3D!'''
    for k in dRHS:
        if k not in dLHS:
            dLHS[k] = dRHS[k]

def cMap(c):
    '''Returns a space if not alpha or space.'''
    if c.isalpha() or c.isspace():
        return c
    if c in "-&.'":
        return ''
    return ' '

def sScrubString(sStr, bToLower=True):
    '''Scrubs the hell out of a string, returns lowercased words with no non alphas'''
    if bToLower:
        sRet = ''.join([cMap(c) for c in list(sStr.strip())]).lower()
    else:
        sRet = ''.join([cMap(c) for c in list(sStr.strip())])
    sRet = ' '.join(sRet.split())
    return sRet

def lsCleanBigrams(sStr):
    import string
    ls = ['']
    for c in sStr:
        if c in string.punctuation and c not in "-&'":
            ls.append('')
        else:
            ls[-1] += c
    ls = [sScrubString(s) for s in ls]
    ls = [s for s in ls if s]
    lsRet = []
    for s in ls:
        lsWords = s.split()
        lsRet += [' '.join(lsWords[i:i+2]) for i in range(len(lsWords) - 1)]
    
    return [s.strip() for s in lsRet if s.strip()]

def lsCleanTrigrams(sStr):
    import string
    ls = ['']
    for c in sStr:
        if c in string.punctuation and c not in "-&'":
            ls.append('')
        else:
            ls[-1] += c
    ls = [sScrubString(s) for s in ls]
    ls = [s for s in ls if s]
    lsRet = []
    for s in ls:
        lsWords = s.split()
        lsRet += [' '.join(lsWords[i:i+3]) for i in range(len(lsWords) - 2)]
    
    return [s.strip() for s in lsRet if s.strip()]

def vPriceIsRightMax(l, v):
    '''returns the greatest element in l that is less than or equal to v'''
    if not [p for p in l if p < v]:
        return min(l)
    return max([p for p in l if p <= v])

def iFindNearest(sText, sSub, i, **kwargs):
    '''Finds the nearest instance of sSub in sText to i.
    Uses liFindAll and passes in any kwargs.'''
    li = liFindAll(sText, sSub, **kwargs)
    li.sort(lambda x, y: cmp(abs(x-i), abs(y-i)))
    if not li:
        return -1
    return li[0]

def lsSplitNWordsIn(sText, iWords):
    '''Takes in text, and returns two substrings.  The first is the first N words, the second is the rest.
    If iWords is negative, counts from the right.'''
    bInSpace = False
    iStep = 1
    iWordsToGo = abs(iWords)
    if iWords < 0:
        iStep = -1
    for i, c in enumerate(sText[::iStep]):
        if c.isspace():
            bInSpace = True
        else:
            if bInSpace: #was in space now is not
                iWordsToGo -= 1
                if iWordsToGo == 0:
                    break
                bInSpace = False
    else:
        if iWords > 0:
            return sText, ''
        else:
            return '', sText
    if iWords > 0:
        return sText[:i], sText[i:]
    else:
        return sText[:-i+1], sText[-i+1:]
    
def lsSplitNSentencesIn(sText, iSentences):
    '''Negative iSentences means count from right.  May munge spaces, and relies on lsSplitIntoSentences.'''
    lsSentences = lsSplitIntoSentences(sText)
    lsRet = '  '.join(lsSentences[:iSentences]), '  '.join(lsSentences[iSentences:])
    return lsRet
        

def lsSplitIntoSentences(sText):
    '''From Mike Smathers (with a few additions by Lisa Gandy :))'''
    sText = sText.lstrip('.')
    sText = sText.lstrip('?')
    sText = sText.lstrip('!')
    abbrevs = ['u.s.','mr.', 'mrs.', 'sen.', 'rep.', 'gov.', 'miss.', 'dr.','ms.', 'lt.']
    abbrevs.extend(['jan.','feb.','aug.','sept.','oct.','nov.','dec.'])
    initial = re.compile('\s[a-zA-Z0-9]\.$')
    
    sentences = []
    p = re.compile(r'([\?\!\.]"?\s+[A-Z0-9"])', re.MULTILINE|re.DOTALL)
   
    m = p.findall(sText)

    idx = 0
    idy = 0
    cand = ''
    hasAbbrev = False
    
    for mm in m:
        idy += sText[idx:].find(mm)+1
        cand += ' '+sText[idx:idy].strip()
        #print "cand %s" % cand
        hasAbbrev = False
        
        if initial.findall(cand, re.MULTILINE|re.DOTALL):#re.findall(initial,cand,re.MULTILINE|re.DOTALL):
           #print re.findall(initial,cand,re.MULTILINE|re.DOTALL)
           hasAbbrev = True
        else:
            for a in abbrevs:
                if cand.lower().endswith(a):
                    hasAbbrev = True
                    break
        
        
            if len(cand) > 2 and not cand[-3].isupper() and cand[-2].isupper() and cand[-1] == '.': #something like J.J.
                hasAbbrev = True
            
        if not hasAbbrev:
            sentences.append(cand.strip())
            cand = ''
        idx = idy

    if idx < len(sText):
        if hasAbbrev == True:
            sentences.append(cand + sText[idx:].strip())
        else:    
            sentences.append(sText[idx:].strip())

    return sentences

#print lsSplitIntoSentences("No way! Props should be given to Rodriguez's breathless 'let's put on a show'? inventiveness.  Plus, William H. Macy and the booger--kick ass!")
#print lsSplitIntoSentences('To see if this dog bowl theory held water, Lt. Eric Keenan, the Bellevue Fire Department\'s community liaison officer, reconstructed the scene. He placed a partially-filled bowl on a wire stand nearly 14 inches above the sun deck at Bellevue City Hall.')
#print lsSplitIntoSentences("The U.S. Federal Communications Commission has heavily promoted the switch to digital TV, with acting FCC Chairman Michael Copps encouraging the move by pointing out that the transition will allow stations to provide more free over-the-air channels than the single channel they've been using under the analog system.")
##assert 0

def iRouletteSelection(llxThings):
    '''llxThings is assumed to be in the form
    [[vThing1, fProb1], [vThing2, fProb2]].  It will do a roulette selection
    over fProbn, and return the index of the winner.  The fProbs don't have to sum to 1 or anything.'''
    fTotal = sum([lx[1] for lx in llxThings])
    f = random.random() * fTotal
    i = -1
    while f > 0.0:
        i += 1
        f -= llxThings[i][1]
    return i

def bIsProgramRunning(sProgram):
    assert sys.platform == 'win32', 'This only works for Windows!  Make a version that uses \'ps -ax\' if you care that much.'''
    lsRunningPrograms = lsCommandLineCall('tasklist')
    for s in lsRunningPrograms:
        if s.lower().startswith(sProgram.lower()):
            return True
    return False

def sDay():
    '''Returns a string of today's day'''
    lsDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return lsDays[time.localtime()[6]]

def sMonth():
    '''Returns a string of today's month'''
    lsMonths = ['NULL', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    return lsMonths[time.localtime()[1]]

def sToday():
    '''Returns a nice printing of the day'''
    return '%s %s, %s' % (sMonth(), time.localtime()[2], time.localtime()[0])

# try:
#     lsMaleNames = [l.lower().strip() for l in open(sPathJoin(FIRST_NAME_DIR, 'malenames.txt'))]
#     lsFemaleNames = [l.lower().strip() for l in open(sPathJoin(FIRST_NAME_DIR, 'femalenames.txt'))]
# except IOError:
#     print 'COULDNT FIND MALE OR FEMALE NAMES!'
#     lsMaleNames, lsFemaleNames = [], []
    
try:
    lsLastNames = [l.lower().strip() for l in open(sPathJoin(LAST_NAME_DIR, 'lastnames.txt'))]
except (IOError, NameError), e:
    lsLastNames = []
    
try:
    lsStopWords = [l.lower().strip() for l in open(PATH_TO_STOP_WORDS_LIST) if not l.startswith('#')]
    dStopWords = dict(zip(lsStopWords, EZGen(True)))
except IOError:
    #print 'DIDNT FIND STOPWORDS!'
    lsStopWords = dStopWords = None
    
try:
    lsDictWords = [l.lower().strip() for l in open(PATH_TO_DICTIONARY_WORDS) if not l.startswith('#')]
    lsDictWords += ["we're", 'I']
    dDictWords = dict(zip(lsDictWords, EZGen(True)))
except IOError:
    #print 'DIDNT FIND DICTIONARY WORDS!'
    lsDictWords = dDictWords = None

try:
    lsProfWords = [l.lower().strip() for l in open(PATH_TO_PROFANITY_LIST) if not l.startswith('#')]
    dProfWords = dict(zip(lsProfWords, EZGen(True)))
except (NameError, IOError), e:
    #print 'DIDNT FIND PROFANITY LIST!'
    lsProfWords = dProfWords = None
    
try:
    lsPosWords = [l.lower().strip() for l in open(PATH_TO_POS_LIST) if not l.startswith('#')]
    dPosWords = dict(zip(lsPosWords, EZGen(True)))
except (NameError, IOError), e:
    #print 'DIDNT FIND POS LIST!'
    lsPosWords = dPosWords = None    
    

def bIsLastName(sWord):    
    return sWord.lower() in lsLastNames
     
def bIsStopWord(sWord, bStrict=False, bIgnoreCase=True):
    '''Takes a word, return True if its a stop word, false otherwise.  Case Insensitive.
    Uses the list at stop_words.lst in ShowShared.'''
    assert dStopWords, 'THe stop word list isnt loaded!  Are you sure stop_words.lst is where I expect , at %s?!?!' % (PATH_TO_STOP_WORDS_LIST)
    if bIgnoreCase:
        sWord = sWord.lower()
    if bStrict:
        return sWord in dStopWords
    sWord = sScrubNonAlNum(sWord)
    for s in sWord.split():
        if s not in dStopWords:
            return False
    return True

def bIsDictionaryWordWiki(word):
    SEARCH_WIKTIONARY = 'http://en.wiktionary.org/wiki/'
    url = SEARCH_WIKTIONARY + word

    try:
        req = urllib2.Request(url, data=None, headers={'User-Agent': 'Mozilla/5.0 (\
    X11; U; Linux i686; en-US; rv:1.9.0.4) Gecko/2008111309Iceweasel/3.0.4 (Zenwalk\
     GNU Linux)'})
        url = urllib2.urlopen(req)
        doc = BeautifulSoup(url.read())
    
        no_art = doc.findAll('div', attrs = {'class': 'noarticletext'})
        if no_art != []:
            #print 'no article'
            return False
        
        langTags = doc.findAll('span',{'class':'mw-headline'})
        for tagB in langTags:
            if tagB.string == "English":
                return True
        return False
        
    except urllib2.HTTPError:
        #print ex
        return False


def bIsDictionaryWord(sWord):
    assert dDictWords, 'COULDNT LOAD DICTIONARY WORD LIST AT %s' % (PATH_TO_DICTIONARY_WORDS)
    return sWord.lower() in dDictWords

def bIsProfanity(sWord):
    assert dProfWords, 'COULDNT LOAD PROFANITY LIST AT %s' % (PATH_TO_PROFANITY_LIST)

    for word in dProfWords:
        c = re.compile(' ' + word + '[^a-zA-z]',re.IGNORECASE)
        
        if re.search(c,' ' + sWord + ' '):
        #if sWord.lower().find(' ' + word.lower() + ' ') > -1:
            #print 'matched word %s' % word
            return True
        
    return False
    #return sWord.lower() in dProfWords

def bIsProfanityRegEx(sWord):
    profList = ['f.*\W+.*ing','sh\Wt','s\W\Wt','sh\Wt','f\W\Wk','fu\Wk','\W\*+\W','b\W\Wch','b\W*i\W*t\W*c\W*h','b\W\W\W\W']
    for word in profList:
        c = re.compile(word,re.IGNORECASE)
        
        if re.search(c,' ' + sWord + ' '):
            if sWord.lower().find(' ' + word.lower() + ' ') > -1:
                print 'matched word %s' % word
            return True
        
    return False



#def bIsVeryPositive(sWord):
#    assert dPosWords, 'COULDNT LOAD POSITIVE LIST AT %s' % (PATH_TO_VERY_POS_LIST)
#    for word in dPosWords:
#        c = re.compile(' ' + word + '[^a-zA-z]',re.IGNORECASE)
#        if re.search(c,' ' +sWord+' '):
#            #print 'matched word %s' % word
#            return True
#        
#    return False
#    #return sWord.lower() in dProfWords



def sTrueCase(text):
    assert dDictWords, 'COULDNT LOAD DICTIONARY WORD LIST AT %s' % (PATH_TO_DICTIONARY_WORDS)
    cap_words = ['President', 'Senator', 'General', 'Bush']
    ret =[]
    for i, word in enumerate(lsSplitAndKeepSpaces(text)):
        bare_word = sStripNonAlNum(word)
        if not bare_word:
            ret.append(word)
        else:
            if bare_word[0].islower():
                ret.append(word)
            elif bIsDictionaryWord(bare_word) or bIsDictionaryWord(bare_word.split("'")[0]) or bIsStopWord(bare_word):
                if not bIsFirstName(bare_word):
                    if not ret or (ret and ret[-1].strip().strip('"').strip("'") and ret[-1].strip().strip('"').strip("'")[-1] in (',', '.', '!', '?')):
                        if bare_word not in cap_words and word[0] != '"':
                            ret.append(word.lower())
                        else:
                            ret.append(word)
                    else:
                        ret.append(word)
                else:
                    ret.append(word)
            else:
                ret.append(word)        
    ret = ''.join(ret)
    return ret

def sForceTitle(sText):
    '''Returns a title-cased version of sText using dictionaries'''
    lsWords = []
    for sWord in sText.split():
        if not bIsFirstName(sWord) and (bIsDictionaryWord(sWord) or bIsStopWord(sWord)):
            lsWords.append(sWord.lower())
        else:
            lsWords.append(sWord[0].upper() + sWord[1:])#can't use sWord.title() here because then we lose the capital P in McPhee
    sRet = ' '.join(lsWords)
    return sRet 

def bIsFirstName(sWord):
    return (sWord.lower() in lsMaleNames) or (sWord.lower() in lsFemaleNames)


def bIsFemaleName(sWord):
    if sWord:
        return sWord.lower() in lsFemaleNames
    else:
        return False
    
def bIsMaleName(sWord):
    if sWord:
        return sWord.lower() in lsMaleNames
    else:
        return False

def bHasLetters(sStr):
    for c in sStr:
        if c.isalpha():
            return True
    return False

def iBestMatch(sMain, lsTexts, bIgnoreCase=False):
    '''Returns the index of the text in lsTexts that is closest to sMain.'''
    lsMainWords = bIgnoreCase and sMain.lower().split() or sMain.split()
    lsMainWords = [sStripNonAlNum(s) for s in lsMainWords]
    
    liCounts = [0] * len(lsTexts)
    for i, sText in enumerate(lsTexts):
        lsTestWords = bIgnoreCase and sText.lower().split() or sText.split()
        lsTestWords = [sStripNonAlNum(s) for s in lsTestWords]
        if lsMainWords == lsTestWords:
            return i #if it's the same make it the best.
        for sWord in lsMainWords:
            if sWord in lsTestWords and not bIsStopWord(sWord):
                liCounts[i] += 1
    iBest, iBestVal = -1, 0
    for iCurr, iVal in enumerate(liCounts):
        if iVal > iBestVal:
            iBestVal = iVal
            iBest = iCurr
    
    return iBest

def lsWordsFromText(sText, bIgnoreCase=False, bIgnoreStopWords=True):
    '''This is used by the two functions below.'''
    lsRet = bIgnoreCase and sText.lower().split() or sText.split()
    lsRet = [sStripNonAlNum(s) for s in lsRet]
    lsRet = bIgnoreStopWords and [s for s in lsRet if not bIsStopWord(s)] or lsRet
    return lsRet

def iStringOverlapCount(sMain, sOther, *args, **kwargs):
    '''Returns the COUNT of words in sMain that are also in sOther'''
    lsMainWords = lsWordsFromText(sMain, **kwargs)
    lsOtherWords = lsWordsFromText(sOther, **kwargs)
#    print 'lsMainWords', lsMainWords
#    print 'lsOtherWOrds', lsOtherWords
#    for sWord in lsMainWords:
#        if sWord in lsOtherWords:
#            print sWord
#    print len(lsMainWords)
    iRet = sum([sWord in lsOtherWords for sWord in lsMainWords])
    return iRet

def fStringOverlap(sMain, sOther, *args, **kwargs):
    '''Returns the PERCENT of words in sMain that are also in sOther.  0<=ret<=1'''
    iMatchCount = iStringOverlapCount(sMain, sOther, **kwargs)
    lsMainWords = lsWordsFromText(sMain, **kwargs)
    
    fRet = lsMainWords and iMatchCount / float(len(lsMainWords)) or 0.0
    return fRet

def fStringOverlapBothWays(sLHS, sRHS, *args, **kwargs):
    f1 = fStringOverlap(sLHS, sRHS, *args, **kwargs)
    f2 = fStringOverlap(sRHS, sLHS, *args, **kwargs)
    fRet = (f1 + f2)/2.0
    #print 'fStringOverlap between %s and %s is %s, %s' % (sLHS, sRHS, f1, f2)
    return fRet

def ifBestMatchBothWays(sMain, lsTexts, *args, **kwargs):
    lfMatches = [fStringOverlapBothWays(sMain, s, *args, **kwargs) for s in lsTexts]
    #for f, s in zip(lfMatches, lsTexts):
    #    print f, s
    iCurrBest, fCurrMax = -1, 0.0
    for i,f in enumerate(lfMatches):
        if f > fCurrMax:
            fCurrMax = f
            iCurrBest = i
    
    
    return iCurrBest, fCurrMax
    
def iSyllablesCalc (word):
        '''counts approximate number of syllables in a word'''
        word_length = len(word)
        lastVowel = 0;
        letter = ' ';
        numSyllables = 0
        
        if word_length <= 3:
            numSyllables=numSyllables+1
        else:
            i=0
            while i<word_length-2:
                letter = word[i];
                if letter in 'aeiouy':
                    if lastVowel == 0:
                        numSyllables=numSyllables+1;
                        lastVowel = 1;
                else:
                    lastVowel = 0;
                
                i=i+1
            #end of for loop from 0 through  next to last character of word
        
            letter = word[word_length-2];
   
            if letter in 'auio':
                if lastVowel==0:
                    numSyllables=numSyllables+1
                    lastVowel=1
                    
            elif letter == 'e':
                lastLetter = word[word_length-1]
                if lastLetter!='s' or lastLetter!='d':
                    if lastVowel==0:
                         numSyllables=numSyllables+1
                         lastVowel=1
            else:
                lastVowel=0;

            letter = word[word_length-1];
            if letter in 'auioy':
                    if lastVowel==0:
                        numSyllables=numSyllables+1
                    
            elif letter == 'e':
                letterBefore = word[word_length-2]
                if letterBefore=='l':
                    if lastVowel==0:
                        numSyllables=numSyllables+1
        
        if numSyllables == 0:
            return 1
                        
        return numSyllables

def stripWords(text):
    text = ' '.join(sXMLUnescape(word.strip()) for word in text.split())
    return text

def _getFile(url,cachedFile=True):
    
    _cache_dir = '/Users/lisagandy/infolab_projects/ccu/cache/'
    assert os.path.isdir(_cache_dir), "zoinks, you forgot to change me to point to a good place for you!"
    """Does some caching too, not threadsafe, nothing fancy, but MC and RT are slow as all hell."""
    assert url, "WHY are you trying to load an empty string url?!?!  Nothing good will come of this!  In fact, I will assure that! %s" % (url)
    md5 = hashlib.md5(url).hexdigest()
    filename = os.path.join(_cache_dir, md5)

    if os.path.exists(filename) and cachedFile:
        # print 'Hit!', filename
        ret = open(filename, 'r').read()
    else:
        # print 'Miss!'
        opener = urllib.FancyURLopener()
        ret = opener.open(url).read()
        # ret = pyU.GetFile(url)
        o = open(filename, 'w')
        o.write(ret)
        o.close()
    return ret

                    
def sStripGETParameters(sURL, lsParamsYouWant=None):
    '''Strips GET parameters off the url, leaving the ones you want.  Case in-sensitive. Returns a new URL
    sRemoveGetParameters('www.google.com?foo=baz&bar=gnar, ['bar']) ==> 'www.google.com?bar=gnar' '''
    if not lsParamsYouWant:
        lsParamsYouWant = []
    iStart = sURL.find('?')
    if iStart < 0:
        return sURL
    sRet = sURL[:iStart]
    lsOrigParams = sURL[iStart+1:].split('&')
    lsParamsYouWant = [s.lower() for s in lsParamsYouWant]
    lsNewParams = []
    for sParam in lsOrigParams:
        if sParam.split('=')[0].lower() in lsParamsYouWant:
            lsNewParams.append(sParam)
    sRet = sRet + '?' + '&'.join(lsNewParams)
    return sRet

def dParseGETParameters(sURL):
    '''Returns a dictionary mapping param name to value, and __URL__ to plain url.'''
    dRet = {}
    iStart = sURL.find('?')
    if iStart < 0:
        dRet['__URL__'] = sURL
        return dRet
    dRet['__URL__'] = sURL[:iStart]
    lsOrigParams = sURL[iStart+1:].split('&')
    for sParam in lsOrigParams:
        dRet[sParam.split('=')[0]] = sParam.split('=')[1]
    return dRet

def test_rss_logger():
    try:
        print 1 / 0
    except Exception, e:
        #oh noes!
        import rss_complainer
        rss_complainer.complain("Something bad happened when dividing! %s" % e)
        
def iLinesInFile(sFilename):
    '''Takes a filename and returns the number of lines in it, probably only works on Linux/OSX'''
    sCommand = 'wc -l %s' % (sFilename)
    try:
        s = lsCommandLineCall(sCommand)[0]
        iRet = int(s.split()[0].strip())
    except ValueError, e:
        print 'EIther couldnt find this file or you dont have the wc program!', sFilename, e
        print 'tried to run', sCommand
        iRet = -1
    return iRet

_urlfinders = [
re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]"),
re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?"),
re.compile("(~/|/|\\./)([-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]|\\\\)+"),
re.compile("'\\<((mailto:)|)[-A-Za-z0-9\\.]+@[-A-Za-z0-9\\.]+"),
] #these are taken from gnome-terminal

def is_url(text):
    '''Returns true if text looks like a url'''
    for urlfinder in _urlfinders:
        if urlfinder.match(text):
            return True
    return False

def sMimeType(fileName):
    
    try:
        fTemp = urllib.urlopen(fileName)
        messageObj = fTemp.info()
        return messageObj.gettype()
    except IOError:
        print "Cannot open file %s in sMimeType" % fileName
        return ""

'''get old one'''
def stripCardinalNum(strNum):
	strNum = strNum.replace('rd','').replace('nd','').replace('st','').replace('th','').strip()
	return strNum.replace('RD','').replace('ND','').replace('ST','').replace('TH','').strip()

if __name__ == '__main__':
    print lsSplitIntoSentences('Hello world!  My name is Nate')

