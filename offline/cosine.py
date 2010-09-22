import math

from pyStemmer import sStem
from pyUtilities import bIsStopWord,removePunctuation,stripExtraSpaces
import re

_documents = {}
_words = {}

def add_document(title, text):
    text = _clean_text(text)
    for word in text.split():
        _words[word] = True
    _documents[title] = text

def clear():
    global _documents, _words
    _documents, _words = {}, {}
        
def classify_document(target_text):
    ret = {}
    target_text = _clean_text(target_text)
    for title, text in _documents.items():
        calculated_similarity, keywords = _similarity(target_text, text)
        ret[title] = calculated_similarity, keywords
    return ret
    
def _clean_text(text):
    reNum = re.compile('\d+')
    text = ' '.join([w for w in text.split() if not bIsStopWord(w)])
    text = sStem(text)
    text = re.sub(reNum,' ',text)
    return stripExtraSpaces(removePunctuation(text.lower()))
    
def _magnitude(model):
    ret = 0
    for count in model.values():
        ret += count * count
    ret = math.sqrt(ret)
    return ret
    
def _similarity(lhs, rhs):
    ret = 0.0
    keywords = []
    lhs = _clean_text(lhs)
    rhs = _clean_text(rhs)
    lhs_words, rhs_words = lhs.split(), rhs.split()
    lhs_model, rhs_model = {}, {}
    for word in lhs_words:
        lhs_model[word] = 1 + lhs_model.get(word, 0)
    for word in rhs_words:
        rhs_model[word] = 1 + rhs_model.get(word, 0)
      
    for word in _words:
        if word in lhs_model.keys() and word in rhs_model.keys():
            ret += lhs_model[word] * rhs_model[word]
            keywords.append(word)
            
    #print lhs_model
    #print rhs_model
    if _magnitude(lhs_model) * _magnitude(rhs_model) > 0:
    	ret /= (_magnitude(lhs_model) * _magnitude(rhs_model))
    else:
        ret = 0

    return ret, keywords

def cos_similarity(lhs, rhs):
    ret = 0.0
    lhs = _clean_text(lhs)
    rhs = _clean_text(rhs)
    lhs_words, rhs_words = lhs.split(), rhs.split()
    lhs_model, rhs_model = {}, {}
    for word in lhs_words:
        lhs_model[word] = 1 + lhs_model.get(word, 0)
    for word in rhs_words:
        rhs_model[word] = 1 + rhs_model.get(word, 0)
      
    #print lhs_model
    #print rhs_model 
    lsWords = lhs_model.keys()
    lsWords.extend(rhs_model.keys())
    _words = list(set(lsWords)) 
    for word in _words:
        if word in lhs_model.keys() and word in rhs_model.keys():
            ret += lhs_model[word] * rhs_model[word]

    ret /= (_magnitude(lhs_model) * _magnitude(rhs_model))
    return ret
    
        
if __name__ == '__main__':

    #add_document('foo', 'dog cat mouse goat')
    #print classify_document('cat parrot')

    add_document('foo','Provider and insurer and regulation businesses reimbursement rates and methods for physicians, insurance companies, or specific procedures, peer review procedures, prospective system (PPS), appeals processes, rates for HMO services, regional adjustments, risk adjustment, reimbursement for chiropractors, foreign medical graduates, nurse practitioners, for outpatient services See also: 325 workforce training programs; 302 insurer or managed care consumer protections.')

    #add_document('bar', 'my name is bar')

    print classify_document('To ensure that the fees that small businesses and other entities are charged for accepting debit cards are reasonable and proportional to the costs incurred, and to limit card networks from imposing anti-competitive restrictions on small businesses and other entities that accept cards.')

    #print classify_document('The companies physicians NATO statement did not list the nationality of the soldiers, but troops fighting in southern Afghanistan are predominantly American and British.')

    #print similarity2('my name is foo and yeah this works','my name is bar and yeah this works')
